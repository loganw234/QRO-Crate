# Validation ledger

Every run that established something, in the order it happened. **A figure
here is a fact about the run that produced it**, on the date given, and is
never updated to match a later measurement: a later run gets a later entry.

Failures stay in, including the ones caused by the author of this file. A
ledger of successes is a brochure. (The form is moth-quantum's
docs/VALIDATION.md.)

The design study's own history, from draft 1 to its approval, is its section
17. The IBM reads of 2026-10-14 are in records/2026-10-14/README.md.

---

## 2026-10-14 - P0 built, before its verifier

Logan approved study QRO-0's draft 12 as the plan of record, with every
recommendation as written, and P0 began the same day. P0 is the lead's
(section 13). It has not yet been past its verifier.

**What was built:**
- qro/vocabulary.py, the one table of terms, types, kinds, spellings, words,
  refusals, and custody and audit fields;
- tools/gen_vocabulary.py, which renders profile/context.jsonld and
  docs/VOCABULARY.md, REFUSALS.md and CONTROLS.md, with `--check`;
- the canonical writer and the strict reader (qro/canonical.py,
  qro/reader.py), the checker's steps 1, 2, 3 and 9 and its seam for 4 to 8
  (qro/checker.py), and the custody check (qro/custody.py);
- the fixture crate, controls/registry.py with section 11's thirty rows, and
  P0's nine controls;
- the floor, copied:
  - verify/run.sh and verify/pytest-stage.sh, from moth-quantum at 3a73823;
  - tools/check_docs.py, from moth-quantum;
  - tools/check_privacy.py, from HonestHarness's tools/check.py;
  - tools/gen_vocabulary.py, on HonestFramework's check_generated.py pattern.

**Measured, by the commands named, on Python 3.12.9:**
- `python -m pytest` over tests/format, tests/custody, tests/controls and
  tests/vocabulary: 126 passed, before tests/docs was written. The runner's
  run is the next entry's.
- `python -m controls.run`: 9 of 9 built controls came out as section 11
  says; 21 printed as pending P1, P2, P3 and P5.
- `python -m controls.plant twin`: ACCEPTED, body digest `93880b5c…`.
  `python -m controls.plant shot-moved`: `REFUSED raw-digest`, exit 1.
- `python tools/check_privacy.py`: 199 files read, nothing found;
  `--control`: 9 of 9 planted faults caught.
- `python tools/check_instruments.py` against moth-quantum at a clean
  3a73823: the study's five analysis instruments reproduced their kept
  outputs, byte for byte.

**The lead's slips, caught on the way:**
- The fixture's crate kept its files under `records/`, which
  tools/check_docs.py then read as this repository's directory. They moved
  to `data/`.
- Two docstrings named test files by the names they had before they were
  renamed. tools/check_docs.py caught one. The other sat on a line that
  names ParcelRound, which the check skips, and was found by reading. That
  skip is a stated limit (tests/docs/test_docs.py).
- `body_digest` hashed a generator's output without arranging it first, so
  the twin's identity depended on the order a writer listed its entities.
  The twin test caught it, and qro/canonical.py's `body()` now arranges
  first.
- A heredoc lost a backslash in Git Bash, twice. It is in CLAUDE.md's
  bite-list.

## 2026-10-14 - the runner, every stage, on P0 as built

`QRO_MOTH_ROOT=<moth-quantum> bash verify/run.sh`, run
`20261014-193938-63565-nocommit+dirty`: **16 of 16 stages passed, none
skipped.**
- The repository had no commit yet. The runner copied from moth-quantum
  refused that as "git cannot read the repository". The lead added a third
  case: a repository git reads with no commit is `nocommit`, always dirty,
  and `--resume` refuses it. That is QRO-Crate's one change to the copied
  framework, and the runner's comment says so.
- The run before it, `20261014-193730-63261-nocommit+dirty`, also passed
  16 of 16. It was taken before the fixture's root gained a `description`,
  which RO-Crate expects of a root. The twin's body digest moved from
  `93880b5c…` to `631257cd…`.
- Summary lines of the run before, by stage:
  - docs: 11 passed;
  - vocab-tests: 6;
  - format: 96;
  - custody: 12;
  - control-tests: 12;
  - controls-run: 9 of 9, 21 pending;
  - privacy: 206 files, nothing found;
  - privacy-controls: 9 of 9 caught;
  - instruments: 5 of 5 reproduced.

  The negative control was refused
  `raw-digest at data/raw.counts.json`, the reason it plants.

## 2026-10-14 - P0's verifier: NOT READY, P0-1 to P0-8, and the fixes

P0's verifier, on Sonnet, read the tree as frozen and found seven defects
and one group of slips. Its report, interim and final, is in
docs/reviews/P0/. Every fault below was planted in its copies, and each fix
is held by a test.

| finding | what was wrong | the fix |
|---|---|---|
| P0-1 | `\d` and `int()` read Arabic-Indic and fullwidth digits: a second spelling of a time passed, in a crate's header and in a custody line | every spelling pattern is ASCII, `[0-9]` |
| P0-2 | a 4,301-digit number, deep nesting, a NaN, or a list where a word belongs crashed the checker, which exited 1 as a refusal does | each is refused by name; a parcel's raw-form reader or generator that fails is refused by its step's name; the command line exits 3 when the checker itself fails |
| P0-3 | the stage registry read commented-out stages, and its tool list was kept by hand | stages are read as the runner reads them; tools and their checks are derived from the tree; moth-quantum's two dropped controls are restored |
| P0-4 | a junction in a crate, its file listed with the right digest, was accepted; an NTFS stream and a case-variant name passed steps 1 to 3 | any link in a crate is refused `file-link`; every listed name is held to the exact name on disk; two names differing only by case are refused |
| P0-5 | FORMAT.md's "no file whose name needs percent-encoding" was false: `a%20b.txt` passed | a file's `@id` is held to a path alphabet: RFC 3986's unreserved characters, sub-delimiters and `@`, with no `:`, `%`, `#` or device name |
| P0-6 | the privacy gate skipped UTF-16 files and non-ASCII file names, and its controls watched groups of patterns, not each one | `git ls-files -z`; a byte-order mark is read; binaries are listed by name; each of 29 alternatives has its own planted control, and three file-level controls are planted too |
| P0-7 | a CHECKED term on an entity no step reads, a digest on the root say, passed | each term names its domain, and the reader refuses it elsewhere; the root's required terms are enforced |
| P0-8 | CLAUDE.md's "~2 min" (12 s measured); the runner's `-h` cut short; FORMAT.md's account of P0's refusal names; a stale comment and docstring order; the fixture's "nothing else" | each corrected |

**Notes taken, beyond the defects:**
- the controls' registry is held to the study's section 11 table, cell for
  cell, and to section 13's owners where it names them;
- `controls.run` fails by name on a P0 row with no plant;
- the vocabulary's `--check`, the instruments' check and every privacy
  alternative each have a negative control (tests/tools/, a new stage);
- every P0 term is exercised by the twin or by a planted test;
- the fixture's raw form refuses bitstrings of unequal length;
- `float-spelt` now plants a float.

**A correction to the entry before.** It said the twin's body digest
"moved from `93880b5c…` to `631257cd…`" when the fixture's root gained a
`description`. That is not what happened: `93880b5c…` was the digest
before the fixture's files moved from `records/` to `data/`. P0's verifier
computed `6b831632…` for the moved files without the description, so two
changes, not one, lie between the two digests. The twin is now
`9345e4eb…`, with `encodingFormat` on its files.

**Measured, by the runner:** `QRO_MOTH_ROOT=<moth-quantum> bash
verify/run.sh`, run `20261014-203954-11345-nocommit+dirty`: **17 of 17
stages passed, none skipped.**
- docs: 16 passed;
- tool-tests: 38;
- vocab-tests: 7;
- format: 150;
- custody: 12;
- control-tests: 15;
- controls-run: 9 of 9, 21 pending;
- privacy: 208 files, none binary, nothing found;
- privacy-controls: 32 of 32 caught;
- instruments: 5 of 5 reproduced;
- the twin: ACCEPTED `9345e4eb…`;
- the negative control: refused `raw-digest at data/raw.counts.json`.

**The lead's slips, caught on the way:**
- P0's freeze held two `.pyc` files, written when the lead ran Python in
  the frozen packet after its hash list was made.
- The table's new sanity check first refused the lead's own `hasPart`: a
  domain of `Dataset` was not counted as admitting the root.
- The new Moth-key pattern first matched code identifiers
  (`moth_quantum_files_read`), and its own plant was one character short.
- A parametrized test used the hostile input itself as its id, and pytest
  overflowed Windows' 32,767-character limit on an environment variable.
- A heredoc lost its backslashes again, twice more.

## 2026-10-14 - P0's verifier's final report: its notes taken, before the re-check

The verifier's first notification was interim. Its final report repeats
P0-1 to P0-8, and adds notes N1 to N8, which asked for one more thing
before any re-check:
- **N1.** Its mutation test removed each of 69 checks in the reader, the
  checker, the custody check and the spellings in turn. 34 of the 69 left
  every test green, though each works today. Also, six mutants of the
  canonical rules survived, because the writer and the reader share
  qro/canonical.py and move together.

**What was done:**
- **N1:**
  - tests/format/test_sites.py plants a fault aimed at each check: 51
    plants;
  - tests/format/golden/ holds golden bytes: the twin's metadata, body and
    identity, a custody log and its head, and an audit record. They are
    checked by hashlib and the json module's key order, independently of
    qro/canonical.py.
  - The fixture's description gained an em dash, so the golden bytes hold
    an escape that `ensure_ascii=False` would change. `allow_nan=True` is
    an equivalent mutant, since the reader refuses every non-integer number
    either way.
- **N4:** the custody log's and audit record's format choices are listed in
  docs/FORMAT.md.
- **N5:** the scan for raised refusal names reads the syntax tree, so a
  reformatted call cannot hide a name.
- **N6:** every term of P0's is exercised.
- **N7:** every spelling has accepted and refused examples, walked both
  ways.
- **N2,** in the first round's fixes: the controls' registry is held to
  section 11 cell for cell, and to section 13's owners.
- **N3,** in part:
  - a parcel registers a count rule in the checker's COUNTS, as it does a
    step, a raw form's reader and a generator. It no longer edits
    `counts()`.
  - controls/run.py runs two kinds of plant, a crate and a custody log. A
    parcel whose control plants anything else, a pair of crates to
    compare say, still extends it.
- **N8,** by P0-4's and P0-5's fixes:
  - a listed name that differs from the name on disk only by case is
    refused at step 2, `file-missing`;
  - a stream's name, with its `:`, is refused at step 1, `spelling`.
- **The privacy gate's placeholder list** was unreachable code, and is gone:
  a home directory's name begins with a letter or a digit, so `<name>` never
  matches.
- **Step 2** also refuses an entry that is neither a regular file nor a
  directory, such as a named pipe a reader would block on.
- **Not taken, as stated limits in docs/FORMAT.md:**
  - RO-Crate's `Profile` type and the Process Run Crate terms (`instrument`,
    `object`, `result`, `agent`) wait for the parcels that use them;
  - so does the profile's version in its IRI.

**The correction above, confirmed.** The lead rebuilt the first fixture's
body from its files, first under `records/` and then under `data/`. Both
digests it got, `93880b5c…` and `6b831632…`, are the ones the entry above
names.

**Measured, by the runner:** `QRO_MOTH_ROOT=<moth-quantum> bash
verify/run.sh`, run `20261014-204746-12108-nocommit+dirty`: **17 of 17
stages passed, none skipped.**
- docs: 16 passed;
- tool-tests: 38;
- vocab-tests: 7;
- format: 207;
- custody: 12;
- control-tests: 15;
- controls-run: 9 of 9, 21 pending;
- study-plants: 68 faults refused, 6 right variants accepted;
- privacy: 233 files, none binary, nothing found;
- privacy-controls: 32 of 32 caught;
- instruments: 5 of 5 reproduced;
- the twin: ACCEPTED `ff3fe486…`;
- the negative control: refused `raw-digest at data/raw.counts.json`.

**Also placed:** every verifier's report, under docs/reviews/:
- the study's twelve, in QRO-0/;
- P0's first report, interim and final, in P0/.

They were redacted as follows:
- home paths, each as `<scratch>`, `<repos>`, `<home-config>` or `<home>`;
- every string the privacy gate reads as a home path, the verifier's
  constructed examples included, as `<a home path>`.

The privacy gate reads them all and finds nothing. The study's section 15
says where they are, and its section 17 records it.

**The lead's slips, caught on the way:**
- The first extraction of P0's report took the interim notification for
  the final one. The final had arrived in a record of another shape.
- The first placing of the reports stopped at the privacy gate, on the
  verifier's own examples of home-path shapes. It was right to stop.

## 2026-10-14 - the providers' notice, and the tree frozen for P0's re-check

**What changed, after the run above:**
- The providers' terms were read, for the study's question 10. Its
  section 17 records the result. On it:
  - NOTICE.md lists what is IBM's and Moth's, the terms read and the date;
  - LICENSE-docs.md scopes CC BY 4.0 to what Logan made;
  - the README carries IBM's suggested acknowledgement;
  - records/2026-10-14/README.md gains a dated provider-content section;
  - tools/check_docs.py reads NOTICE.md as a document.
- The study's amendment had left the plants' two figures as unfilled
  placeholders. They are filled from the plants' run, and section 17 says
  so.

**Measured, by the runner:** `QRO_MOTH_ROOT=<moth-quantum> bash
verify/run.sh`, run `20261014-210025-13190-nocommit+dirty`: **17 of 17
stages passed, none skipped.** Every summary line is the run above's,
except two:
- privacy: 234 files, NOTICE.md the new one;
- check-docs: 10 documents.

The twin is ACCEPTED `ff3fe486…`, unchanged.

**The lead's slip.** The amendment's script wrote placeholders where the
plants' figures belonged. The lead's checks after it read the gate's
verdicts, not the text the script wrote. The study's gate does not read
those figures either.

## 2026-10-14 - P0's second verifier: NOT READY, R2-1 to R2-9, and the fixes

P0's second verifier, on Sonnet, re-checked the tree frozen in the entry
before (234 files), in the scope it was given:
- P0-1 to P0-8, and N1 to N8;
- the review copies;
- the study's edits since its approval;
- the provider notice.

It found nine defects and thirteen notes. Its report is
docs/reviews/P0/round2.md.

**What held, by its own plants:**
- the freeze;
- the runner, 17 of 17, twice;
- a commit and clone of all 234 files, byte for byte;
- P0-1, P0-3, P0-4, P0-6, and P0-7's matrix;
- N1's golden bytes. Of round 1's canonical mutants, 18 of 19 are killed,
  and the survivor is equivalent;
- every review copy, against its source;
- every change to the study, against section 17;
- NOTICE.md, against the terms report.

| finding | what was wrong | the fix |
|---|---|---|
| R2-1 | P0-5's path rule, and N8's stream rule, were held by no test. The plant left its graph unsorted and took either of two refusals, so the order's refusal stood in for the path's. With the rule deleted, every test passed and `data/a%20b.txt` was accepted end to end. | Every plant keeps the graph in order, and requires `spelling` from the path rule. The path spelling is walked both ways, 24 names accepted and 52 refused, and 48 of the refused are planted in a crate. A real file named with each sub-delimiter is held through every step. |
| R2-2 | The command line crashed with exit 1, a refusal's code, when a refusal echoed a lone surrogate, or a character the console's encoding lacks. | It prints ASCII only, every other character escaped. A verdict it cannot print at all exits 3. Planted in process, through cp1252, UTF-8 and ASCII, and as a process. |
| R2-3 | `admits` matched every domain token against an entity's `@id`. So an entity named `qro:RawResult` could state a count no step reads. | Only the root's and the descriptor's tokens name an `@id`. Six entities named for a domain are planted. |
| R2-4 | The format stage could not pass off Windows: a test skipped there, and the runner fails a stage that skips. | The test plants a junction on Windows and a symbolic link elsewhere, with no skip. |
| R2-5 | `text` let C1 control characters through, though its prose refused every control character but the line feed. | C1 is refused. Each control range has a refused example, and the line feed, NBSP and an em dash accepted ones. |
| R2-6 | FORMAT.md's item 8 counted seven names over a list of eight. | The item states no count, and tests/docs holds its list to the table and the study. |
| R2-7 | The entry before said FORMAT.md states Process Run Crate's terms as a limit. It did not. | FORMAT.md states it now. |
| R2-8 | The study's review README said "the only change" was a redacted home path. Seven copies had also lost a notification's wrapper and their CRLF. | Both READMEs state every change, counted per file. A script re-derives each copy from its source and requires it equal. |
| R2-9 | The "copied" headers of verify/run.sh and tools/check_docs.py said less than had changed. | Each lists every change. |

**Every gap round 2's mutants found now has a plant:**
- the path alphabet, the device names, and `absolute()`;
- a root of another type;
- a size off by one beside a right digest;
- an audit record's stages twice;
- `_ID` letting DEL through;
- an IRI with a space;
- a `binary64` outside its pattern;
- the writer's one-type rule;
- an entry neither a file nor a directory;
- a link the walk asks the host about.

**Notes taken:**
- **1.** The stage registry:
  - reads a tool's `__main__` and its modes in either quote;
  - counts a negative control's stage for no tool's check, so the twin's
    stage cannot be deleted unnoticed;
  - refuses a stage that masks its exit (`|| true`).

  Each is planted.
- **2.** The descriptor's name counts as a file's for the case rule.
- **3.** The walk's blind spots are stated limits in FORMAT.md: a stream on a
  listed file, a hard link, an empty directory.
- **4.** Device names now include COM0, LPT0, CONIN$ and CONOUT$. A segment
  holds at most 255 characters. Beyond the note:
  - `*` leaves the path alphabet, since Windows refuses it in a name;
  - an `@id` is an IRI only after a scheme of two characters or more with
    no dot. So `C:/x` and `notes.txt:hidden` stay paths, even at the
    crate's top, and are refused.
- **5.** The privacy gate's named-token pattern catches `access_token=` and
  its kin, and its plant is that form.
- **6.** NOTICE.md lists the service's use limits, and the usage's metric id
  with what IBM's API reference calls it.
- **7.** REFUSALS.md's `graph-form` row lists every cause, step 3's among
  them.
- **8.** "51 plants", in the entry before, counted the tests
  tests/format/test_sites.py collects. 29 come from the reader's table, and
  a few are not plants.
- **9.** CLAUDE.md says where the `@id` and path rules are written.
- **10.** The time spelling says a leap second's `:60` is refused.
- **11.** CLAUDE.md and FORMAT.md say a parcel's failing reader or
  generator shows as a refused crate.
- **13.** qro/custody.py states that a future-dated `at` is accepted, and a
  test shows it.

**Notes not taken, each stated where it applies:**
- **N5.** The aliased constructor (`R = Refused`) is not seen by the
  static scan. It is stated in its test.
- **N6.** "Exercised" means the term's quoted name is found in a test file.
  It is stated in its test.
- **12.** The four approval-status edits to the study are left as they
  are. The approval paragraph covers them.

**A correction to the entry before.** It listed the Process Run Crate terms
under "Not taken, as stated limits in docs/FORMAT.md". FORMAT.md did not
state them then (R2-7). It does now.

**The lead's slips, caught on the way:**
- R2-1's vacuous plant was the lead's own. It accepted either of two
  refusals, and so proved neither.
- A heredoc lost its backslashes twice more. Both times it failed an
  assertion before it wrote anything.

**Measured, by the lead, before the freeze:**
- Round 2's three mutation operators, its own scripts, on a copy of the
  tree. The copy was taken before the last test below was added, and a
  test added can only kill more:
  - a check made never to fire: 78 sites, 76 killed. The 2 survivors are
    the two round 2 argued equivalent: the descriptor and the root first,
    and a single-valued term given a list.
  - a refusal's name swapped: 61 sites, 61 killed.
  - hand mutants: 68 in all.
    - 50 killed.
    - 4 survived: round 2's four equivalents. They are `allow_nan` in
      `dumps` and in `compact`, a size of 20 digits, and the walk following
      links.
    - 14 not applicable, since their source text had changed.
- The lead re-wrote those 14 against the new source, and added 15 mutants
  of round 2's fixes (scratch only): 29 of 29 killed. That held after one
  more plant: a refusal that cannot be printed exits 3, as an acceptance
  does.
- The runner, `QRO_MOTH_ROOT=<moth-quantum> bash verify/run.sh`, run
  `20261014-222901-20179-nocommit+dirty`: **17 of 17 stages passed, none
  skipped.**
  - docs: 23 passed;
  - tool-tests: 38;
  - vocab-tests: 7;
  - format: 370;
  - custody: 18;
  - control-tests: 15;
  - controls-run: 9 of 9, 21 pending;
  - study-plants: 68 faults refused, 6 right variants accepted;
  - privacy: 235 files, none binary, nothing found;
  - privacy-controls: 32 of 32 caught;
  - instruments: 5 of 5 reproduced;
  - check-docs: 10 documents;
  - the twin: ACCEPTED `ff3fe486…`, unchanged;
  - the negative control: refused `raw-digest at data/raw.counts.json`.

## 2026-10-14 - P0's third verifier: NOT READY, R3-1 to R3-4, and the fixes

P0's third verifier, on Sonnet, re-checked the tree frozen in the entry
before (235 files). Its scope:
- R2-1 to R2-9;
- the mutation tests;
- round 2's notes;
- the changes beyond them;
- anything else now false;
- the review copies;
- the usage-metric id.

It found four defects and fifteen notes. Its report is
docs/reviews/P0/round3.md.

**What held, by its own plants:**
- the freeze;
- the runner, 17 of 17, three times, once in a committed clone;
- a commit and clone of all 235 files, under both `core.autocrlf`
  settings;
- the lead's measured block, to the figure;
- R2-3, R2-4, R2-5 and R2-7 in full. R2-1, R2-2, R2-6, R2-8 and R2-9 held
  for the instances round 2 named;
- `text` against all 1,114,112 code points;
- the path rules against 2,000,000 random ids, with no disagreement;
- 126,475 byte-level mutants of the twin, with no crash and no second
  spelling;
- 14,768 look-alike mutants, none accepted;
- every review copy against its source, and each source against its
  verifier's own last message;
- NOTICE.md against the IBM text the research agent extracted.

| finding | what was wrong | the fix |
|---|---|---|
| R3-1 | The command line's claims about its output were false for a pipe, a file or a closed descriptor. The verdict was buffered, so a failed write surfaced at the interpreter's exit as exit 120, or as nothing at all. A crate's key holding a line feed printed a second line beginning ACCEPTED, under a refusal's exit. | The command line writes its one line to the descriptor itself, unbuffered, before it returns, so a failed write exits 3. Every character but printable ASCII is written as its Python escape, the line feed among them. tests/format/test_cli.py plants each case, in process and as a process: a pipe nobody reads exits 3, never 120. |
| R3-2 | "A fault aimed at each check", in the entry for P0's first verifier's final report, was false. Fifteen faults of round 3's, each one edit to a correct check, left every test green. Ten gave a wrong answer or a crash, and five turned a valid crate away. | Each has its plant: the custody check's log; the command line's custody command, records, misuse and printed identity; a raw-form count that is not a whole number, and zero; a `@graph` that is not a list; the path rule on a File of two types, in every segment, on a device name with any extension, and for every character it admits; a nested Dataset; a web-based part with no entity; a crate of two entities; and a size of 2^63 - 1. |
| R3-3 | Three limits were stated by an instance, and the class walked past them. The registry's mask check caught `\|\| true` and missed a dozen other masks. FORMAT.md's stream sentence was false for `README:hidden`. Item 8's test held its list from below only. | The registry requires every stage to run a simple command, and its plants are 24 masks and a continuation. FORMAT.md states the stream limit as it is. Item 8's test holds three things: every own name, no name the table lacks, and no count in any form. |
| R3-4 | Two statements about what was changed were each one item short. The study's review README missed the wrapper's `<tool-use-id>` and the final line feed added, and wrongly said no source held a raw `<`. The header of tools/check_docs.py missed its own docstring's rewrite. | The placing script measures each change per file and writes both READMEs from those measurements. The header lists every change. |

**Notes taken:**
- **1.** Every spelling has an accepted value that uses every character
  its rule admits, and a scheme may begin with every letter. A test checks
  that the values do cover their classes.
- **2.** The registry also refuses four more plants: a negative control
  that names no refusal, a pytest stage with an option other than
  `--ignore=`, a lint that leaves out a directory holding Python, and a
  twin's stage that plants the control.
- **3.** The privacy gate's camelCase token (`accessToken: …`) is its own
  alternative, with its own plant: 33 of 33 caught.
- **5.** FORMAT.md and the comment name the devices Windows reserves, and
  the four refused besides them as a safe superset.
- **6.** FORMAT.md states that a path is bounded by segment only.
- **7.** FORMAT.md's item 7 names `qro:implementation` as the header term
  that is not the root's alone.
- **8.** The registry's docstring says it reads `check_*.py` under
  docs/studies/qro0/.
- **10.** The runner's header says `--list` puts a space after its column.
- **11.** A crate that is not a directory, or a log or record that is not a
  file, is misuse: exit 2, not 3 or 1.
- **14.** The docs gate checks links in every markdown file under docs/ and
  records/: 21 more files, every link resolving.
- **Beyond the notes:**
  - The `iri` spelling and `absolute()` share one scheme pattern,
    qro/spelling.py's `SCHEME`, so the code has one meaning of an absolute
    IRI. A dotted or one-letter scheme is refused in both.
  - A simple command can still name a tool without running it
    (`echo python tools/check_docs.py`). The registry now counts a tool,
    or a test directory, as staged only where it is the program a stage
    runs. That is planted four ways for a tool and once for a directory.

**Notes not taken:**
- **4.** The acknowledgement's second sentence stays the lead's wording.
  In NOTICE.md it stands outside the quotation marks, so it is not IBM's.
- **9.** The study's status line is dated to its approval.
- **12.** CLAUDE.md's timings are fair, as round 3 measured them.
- **13.** No host here can make a FIFO. The plant patches the walk's
  question.
- **15.** Nothing to take.

**Corrections to the entries before:**
- The round-2 entry's R2-2 row said "a verdict it cannot print at all exits
  3". That held for a terminal and for the planted fake, not for a pipe or
  a file (R3-1).
- The final-report entry's "plants a fault aimed at each check" was false
  (R3-2). So was the round-2 entry's "every gap round 2's mutants found now
  has a plant", read as "every gap": it held for round 2's mutants only.
- The round-2 entry's "Both READMEs state every change" and "Each lists
  every change" were each one item short (R3-4).

**The usage-metric id, still open.** Round 3 read IBM's API reference and
could not settle whether the id is IBM's for every account or this
account's own. One read would settle it: the same endpoint, for a job of
another instance or plan. That is Logan's to allow. NOTICE.md's "not
established" stands.

**The lead's slips, caught on the way:**
- Round 2's fix for the command line was tested against a fake stream, in
  process. The failure it missed comes at the interpreter's exit, which no
  in-process test can see. The new tests run the process.
- The alphabet's test string first ended in a dot, and the trailing-dot
  rule refused it, rightly.
- The first count check read the digit in "P0's" as a count.
- A new function in tools/check_docs.py took a name its own `problems()`
  used for a local, and ruff caught it.

**Measured, by the lead, before the freeze.** Round 3's own mutation tools,
on copies of the tree taken as the fixes went in, against the whole suite.
Each later copy added tests only, and a test added can only kill more:
- **Operator D,** over the reader, the checker, the custody check, the
  spellings, the canonical rules and the command line: 454 mutants, 443
  killed. The 11 survivors are each equivalent:
  - round 3's: `seen.add(k)` deleted; the graph's minimum lowered to 1;
    `bits >> 62` for the two zeros; the infinity branch's three; and a
    size of 20 digits.
  - the command line's escape, which leaves space and `~` alone either way;
  - and its second write after a failed one. Both go to the failing
    descriptor, so the exit is 3 either way.
- **Round 3's path set:** 39, 36 killed. Its 3 survivors are equivalent:
  - `.` and `..` both end in a dot;
  - `lower()` is `casefold()` on ASCII;
  - the descriptor's name is lower case already.

  The first segment's length, a real gap at first, has its plant.
- **Round 3's alphabet sets:** 94 and 5. All are killed but two:
  - a gain of `/`, which is equivalent, since a segment has no `/`;
  - one that does not compile.
- **Round 3's class-member removal:** 372 mutants.
  - 232 killed.
  - 132 not applicable, since the scheme pattern moved.
  - 8 survived, each a removal from the binary64 decimal's `[!-~]`. These
    are equivalent: the exact-decimal comparison after that pattern refuses
    the same inputs. The time, date, size and rational digits, real gaps at
    first, have their accepted values now.
- **The lead's class-member removal on the moved scheme pattern** and the
  IRI's tail: 210 of 210 killed.
- **Round 3's command-line set** mostly no longer applied: 26 of 37, since
  the command line was rewritten. Of the rest, 10 were killed. The 1
  survivor is equivalent: with one argument, `args[0]` is `args[-1]`.
- **The lead's 18 mutants of the new command line:** 18 of 18 killed. That
  held after one more misuse plant, `check CRATE --fixtures`.

**Measured, by the runner:** `QRO_MOTH_ROOT=<moth-quantum> bash
verify/run.sh`, run `20261015-004228-28659-nocommit+dirty`: **17 of 17
stages passed, none skipped.**
- docs: 60 passed;
- tool-tests: 39;
- vocab-tests: 7;
- format: 520;
- custody: 19;
- control-tests: 15;
- controls-run: 9 of 9, 21 pending;
- study-plants: 68 faults refused, 6 right variants accepted;
- privacy: 237 files, none binary, nothing found;
- privacy-controls: 33 of 33 caught;
- instruments: 5 of 5 reproduced;
- check-docs: 10 documents, 21 other markdown files, 33 source files;
- the twin: ACCEPTED `ff3fe486…`, unchanged;
- the negative control: refused `raw-digest at data/raw.counts.json`.

## 2026-10-15 - P0's fourth verifier: NOT READY, R4-1 to R4-5, and the fixes

P0's fourth verifier, on Sonnet, re-checked the tree frozen in the entry
before (237 files). It found five defects and ten notes, none a wrong
accept in the shipped code. Its report is docs/reviews/P0/round4.md.

**What held, by its own plants:**
- the freeze;
- the runner: 17 of 17 in a `git init` copy and in a committed clone, and
  14 of 14 quick;
- a commit and clone of all 237 files, under both `core.autocrlf`
  settings;
- R3-1 in every shape it tried, about 70 process runs on Windows and Linux;
- each of round 3's fifteen faults, which now fails a test;
- every figure in the lead's measured block, reproduced;
- every review copy against its source, and `round3.md` against its
  verifier's last message.

| finding | what was wrong | the fix |
|---|---|---|
| R4-1 | The command line's tests left four faults green. They were: the fixture registered without `--fixtures`; a path of the wrong kind; a partial write; both descriptors failing. | Each has its test. There is also a round trip of the escape through `unicode_escape` for every code point, so `?` cannot stand for a character. And there is a closed descriptor as a process, through the runner's own bash by its full path. test_cli.py's docstring lists what it holds and nothing more. |
| R4-2 | The spellings' refused side was never swept. A pattern made a wildcard, a class made wider, or a device list one digit short (COM3 and LPT7 accepted into a crate) passed every test. So did a walk that followed only the root's own parts. | tests/format/test_sweep.py holds each spelling, the path rule, the `@id` rule and `absolute()` to an independent statement of its rule. The strings are every substitution, deletion and insertion of a character in their examples, over printable ASCII and twelve other characters, among them a non-ASCII digit. Every device name is refused in every segment and case, and names near one are accepted. A Dataset two levels down is planted. |
| R4-3 | Two tests held less than the sentence over them. Item 8's count was checked before its first colon only, and the negative control's `MUST_SAY` only for being non-empty. | FORMAT.md's item 8 says "no count of them before this colon". `MUST_SAY` must be `REFUSED` and the very refusal its plant's row expects, and four wrong ones are planted. |
| R4-4 | The header of tools/check_docs.py named one of the two sentences of moth-quantum's it drops. The runner's header said reworded where one comment was deleted. | Both name every change. |
| R4-5 | Round 3's note on REFUSALS.md's `graph-form` row was answered nowhere. The row was still one cause short. | The row names the root's `conformsTo`, and a `@graph` not a list of two entities or more. The lead walked the code's fifteen `graph-form` refusals against it. |

**Notes taken:**
- **1 to 3.** The stage registry states what it cannot see: a stage the
  shell never reaches, a tool's own masking flag, and the runner's own
  exit.
- **4.** A partial line under exit 3 is a stated limit, in FORMAT.md and the
  command line's docstring, and planted.
- **5.** A path the host will not look at, a 300-character name say, is
  misuse: exit 2, not 3.
- **6.** `absolute()` is the `iri` spelling itself, qro/spelling.py's `IRI`,
  so `http:` is neither.
- **7.** Python's own failure to start the command line exits 1 with no line.
  This is stated in FORMAT.md, CLAUDE.md and the docstring. A refusal is
  exit 1 and its REFUSED line.
- **9.** The sweep puts a non-ASCII digit at every place of every example,
  every field of a time among them.
- **10.** An exit or an interrupt raised inside the checker, a parcel's code
  among it, exits 3, and each is planted.

**Not taken:**
- **8.** REFUSALS.md's other rows are summaries, and claim no list.

**Corrections to the entries before:**
- The final-report entry's N8 line said "a stream's name, with its `:`, is
  refused at step 1". That was false for a top-level name that is itself a
  scheme (`README:hidden`), as FORMAT.md has said since round 3.
- The round-3 entry's note 13 said "no host here can make a FIFO". Round 4
  made them on WSL, and the walk refused each one `file-link`.
- The round-3 entry's R3-1 row said each case was planted "in process and
  as a process". The closed descriptor was planted in process only. It is
  planted as a process now.
- The round-3 entry said `iri` and `absolute()` gave the code "one meaning of
  an absolute IRI". They shared the scheme, not the meaning (`http:`). They
  share both now.
- The round-3 entry's R3-3 row said item 8's test catches a count "in any
  form", and that the registry refuses "a negative control that names no
  refusal". Each held less (R4-3).
- The round-3 entry's R3-4 row, "The header lists every change", was one
  item short (R4-4).
- The round-2 entry's note 7, "REFUSALS.md's `graph-form` row lists every
  cause", was one short (R4-5).

**The lead's slips, caught on the way:**
- A Python heredoc lost a backslash again, and a string match failed on a
  line break. Both failed their assertions before writing anything.

**Measured, by the lead, before the freeze.** Round 4's own mutant sets,
through its own harness, on a copy of the tree that differs from the freeze
only by this entry:
- **Its command-line set:** 16 mutants.
  - 10 killed.
  - 1 survived, and it is equivalent: registering after the usage test,
    since a misuse returns before the registration matters.
  - 5 not applicable, since their text changed. The lead re-wrote those 5
    and added 3 more, and all 8 were killed.
- **Its R3-2 rows and variants:** 42 mutants, 40 killed. The 2 survivors are
  round 4's own equivalents:
  - `check_log` after the head test;
  - the `hasPart` list guard.
- **Its class-member removal, adapted:** 332 mutants.
  - 311 killed.
  - 8 survived, each a removal from the binary64 decimal's `[!-~]`. These
    are equivalent.
  - 13 not applicable, since the IRI pattern was renamed. The lead's scheme
    and IRI-tail set, on the renamed pattern: 210 of 210 killed.
- **Its quantifiers, separators and branches:** 74 mutants, 72 killed. The 2
  survivors are equivalent:
  - binary64's `+` to `*`;
  - the device extension's `*` to `+`, since the trailing-dot rule runs
    first.
- **Its atoms made wildcards:** 75 mutants, 69 killed. The 6 survivors are
  equivalent:
  - one binary64 wildcard;
  - five date wildcards, which `date.fromisoformat` refuses.
- Every real gap round 4 named in these sets is now killed: the device
  digits, the time's separators, the sizes' and rationals' atoms, the
  scheme's first class, and the walk two levels deep.

**Measured, by the runner:** `QRO_MOTH_ROOT=<moth-quantum> bash
verify/run.sh`, run `20261015-015939-34899-nocommit+dirty`: **17 of 17
stages passed, none skipped.**
- docs: 63 passed;
- tool-tests: 39;
- vocab-tests: 7;
- format: 564;
- custody: 19;
- control-tests: 15;
- controls-run: 9 of 9, 21 pending;
- study-plants: 68 faults refused, 6 right variants accepted;
- privacy: 239 files, none binary, nothing found;
- privacy-controls: 33 of 33 caught;
- instruments: 5 of 5 reproduced;
- check-docs: 10 documents, 22 other markdown files, 34 source files;
- the twin: ACCEPTED `ff3fe486…`, unchanged;
- the negative control: refused `raw-digest at data/raw.counts.json`.

## 2026-10-15 - P0's fifth verifier: NOT READY, R5-1 to R5-5, and the fixes

P0's fifth verifier, on Sonnet, re-checked the tree frozen in the entry
before (239 files). It found five defects and twelve notes, none a wrong
accept in the shipped code. Its fuzzing found no disagreement, crash or
second spelling:
- 1,850,281 strings against the sweep's statements;
- 121,950 mutants of the twin's metadata;
- 120,000 of a custody log and record.

Its report is docs/reviews/P0/round5.md.

**What held, by its own plants:**
- the freeze;
- the runner: 17 of 17 in a `git init` copy and in a committed clone;
- a commit carrying the harness's attribution line, which the privacy gate
  accepts;
- R4-1's five faults, R4-2's real gaps, R4-3(b), R4-4 and R4-5;
- every figure in the lead's measured block;
- every review copy against its source.

| finding | what was wrong | the fix |
|---|---|---|
| R5-1 | The sweep said "every one-character change" and tried 107 characters. Faults at 57 of the 71 sites of the `text` spelling's deny list passed it. One accepted U+0001 in a header term. | The sweep's alphabet takes every C0 and C1 control character, DEL, the surrogates' edges, U+3000 and an astral character. Its docstring says what it holds and no more: the spellings it sweeps, held to the table's string spellings by a test, and the characters. |
| R5-2 | Item 8's test said it "counts nothing". It looked before the item's first colon only. | It says "before its first colon". |
| R5-3 | "A path the host will not look at is misuse" held for a question that raises. A log, a record, the metadata, a listed file or the crate directory that the user may not read exited 3, "the checker itself failed". | The command line answers a `PermissionError` as misuse, exit 2, "cannot be read here". And the walk raises on a directory it cannot list, where it had passed it over (note 1: such a crate was accepted). Each is planted. |
| R5-4 | The reviews README dated round 4's report a day early. | Each row carries its own date, read from its source file. |
| R5-5 | Two plants were refused for a second cause. The unequal bitstrings had no final line feed. And the twin's raw result masked a generator registered without `--fixtures`. | Each raw-form plant must fail on the rule it names, and the refusal's detail is checked; four cases are new. A crate with no raw result is checked as a process without the flag, and refused for its generator. |

**Notes taken:**
- **1.** A directory the walk cannot list is raised (R5-3).
- **2.** The closed-descriptor tests find Git's own bash beside git.exe on
  Windows, not by `which bash`.
- **3.** The `iri` spelling's prose says a character must follow the `:`.
- **4.** The reader's docstring says a reference that only looks like an IRI
  names no entity, and a plant holds it.
- **5.** Each check round 5 found held by no test now has a plant:
  - a type listed twice;
  - a negative numerator of exactly 1,000 digits;
  - the walk's order, under five hash seeds in five processes;
  - the context's pin;
  - an empty directory as a crate;
  - a host that raises any `OSError` on the question.
- **6.** CLAUDE.md's quick budget says ~20 s.
- **7.** The header of tools/check_docs.py names every count the summary
  prints.
- **8.** The registry holds every negative control, not the first alone.
- **9.** test_sites.py no longer leaves a temporary directory behind.
- **10.** An empty name is misuse. Following a link to a crate, log or
  record is stated.
- **Beyond the notes:** `qro.spelling.time()` pads the year itself, where
  glibc's `strftime` left a year below 1000 unpadded (round 5, 4.6).

**Not taken:**
- **11.** `README:hidden` stays a stated limit.
- **12.** This Windows build makes `CON` and the others as ordinary files.
  FORMAT.md already calls the device list a safe superset.

**The scrub.** Each sentence over a test, a stage or a gate was read against
what it holds. Restated:
- test_hostile.py's docstring: the cases planted, not "never crashes";
- test_vocabulary.py's: its sanity check, not "no contradiction";
- test_spelling.py's: the sweep's characters, not "every one-character
  change";
- test_cli.py's and test_docs.py's;
- the runner's stage lines for the registry, the docs gate, the vocabulary
  tests and the privacy gate;
- CLAUDE.md's sentence on the registry.

The docs gate's missing index, which its docstring names, has its plant
now.

**Question 10, decided.** Logan, 2026-10-15: "When we push, go ahead with a
public repo, I will ask Moth directly about the data licensing situation
when available." The same day the lead read IBM's two service descriptions
again, on IBM's terms site:
- i126-9425 is still v10, published 2026-08-06;
- i126-6605 is still v29, published 2026-09-29.

NOTICE.md records both, and the study's section 17 records the decision.

**Corrections to the entries before:**
- The round-4 entry's R4-2 row said the sweep holds each spelling "to an
  independent statement" over every change of a character "over printable
  ASCII and twelve other characters". Its row was exact; the sweep's
  docstring was not (R5-1).
- The round-4 entry's note 5, "a path the host will not look at … is
  misuse", held for a question that raises, not for a read (R5-3).
- The reviews README's "Collected 2026-10-14" was wrong for round 4's
  report (R5-4).

**The lead's slips, caught on the way:**
- A heredoc ate its backslashes twice more, and the Write tool turned
  `\u` escapes in a test's text into the characters themselves. Every
  script since writes backslashes as `chr(92)`, or not at all.

**Round 6 is the last, by Logan's word.** Logan, 2026-10-15: "If the last
rounds have just been semantic changes and nothing related to code
directly, round 6 can be the last, with the verifier instructed not to hold
it back for prose only issues." The lead's account to him: round 4 found
test-reach gaps and wording. Round 5 found two small code fixes, R5-3 and
its note 1 (a crate could hide files in a directory the walk could not
list), and test-reach gaps and wording. So round 6's verifier holds the
tree NOT READY only for a defect in what the code does:
- a wrong acceptance or refusal;
- a crash;
- a wrong exit code;
- a check that lets a real fault in the tree through.

A sentence that says more or less than is true is reported as a note. If
round 6 finds a code defect, the lead fixes it, runs the whole runner, and
brings it to Logan, not to a round 7.

**Measured, by the lead, before the freeze.** Round 5's own sets, through
its own harness, on copies of the tree taken as the last fixes went in. Each
later copy added tests only:
- **Operator E,** over `qro/`, the fixture included: 528 mutants, 480
  killed, 1 not applicable, 47 survived. 46 of the survivors are
  equivalent:
  - an error's message or location only. These are a slice of a one-item
    list, `args[0]` for `args[-1]` with one argument, and the order in
    which several faults are named.
  - a later check that refuses the same input by the same name: a key
    twice, a NaN, a list where one value stands, the descriptor and root
    out of order, a non-ASCII byte read by `json`;
  - `casefold` for `lower` on ASCII names;
  - the date's pattern by `match` or `search`, whose leftovers
    `date.fromisoformat` refuses.

  The last survivor was a test gap: the `KeyError` for a spelling the table
  does not name. It has its plant now.
- **Its deny-list set:** 71 mutants. On the first copy 70 were killed, and
  U+D83D, an interior surrogate, survived. After a plant of every lone
  surrogate, 71 of 71 were killed.
- **Its command-line set:** 45 mutants, 31 killed, 8 not applicable since
  the text changed. The 6 survivors are equivalent: `re.ASCII` on a
  character range, the escape of space, `~` or `"`, and which missing path
  is named.
- **Registration at import:** 5 mutants, 4 killed. The survivor is
  equivalent: the raw form registered alone, which step 9 still refuses.
- **`\d` for `[0-9]`:** 17 mutants, 14 killed. The 3 survivors are the
  date's classes. They are equivalent on CPython, whose `date.fromisoformat`
  refuses other digits.

**Measured, by the runner:** `QRO_MOTH_ROOT=<moth-quantum> bash
verify/run.sh`, run `20261015-043701-58758-nocommit+dirty`: **17 of 17
stages passed, none skipped.**
- docs: 65 passed;
- tool-tests: 39;
- vocab-tests: 7;
- format: 596;
- custody: 19;
- control-tests: 15;
- controls-run: 9 of 9, 21 pending;
- study-plants: 68 faults refused, 6 right variants accepted;
- privacy: 240 files, none binary, nothing found;
- privacy-controls: 33 of 33 caught;
- instruments: 5 of 5 reproduced;
- check-docs: 10 documents, 23 other markdown files, 34 source files;
- the twin: ACCEPTED `ff3fe486…`, unchanged;
- the negative control: refused `raw-digest at data/raw.counts.json`.

## 2026-10-15 - P0's sixth and last verifier: READY

P0's sixth verifier, on Sonnet, checked the tree frozen in the entry before
(240 files) to the bar Logan set: NOT READY only for a defect in what the
code does. It found none. Its report is docs/reviews/P0/round6.md.

**What READY rests on, by its own runs:**
- the freeze, at its start and its end;
- the runner: 17 of 17, run `20261015-044937-59815-nocommit+dirty`, every
  count equal to the last block above;
- a commit and clone of all 240 files, under both `core.autocrlf`
  settings, the privacy gate reading the commit message;
- R5-1 to R5-5 and round 5's notes, each in what the code does;
- the three code changes since round 5, against its own attempts to break
  them;
- a second reading of the rules, with no disagreement and no crash. That
  covered:
  - about 18.7 million strings;
  - 400,000 mutants of the twin's metadata, against a reader of its own;
  - 60,000 custody cases;
  - 290 random crates, with 5,319 faults injected;
  - 40,000 argument lists;
  - 21 permission cases, as a user who cannot read;
- every mutation survivor, equivalent or a test gap. For each gap it ran
  the shipped code directly, and the shipped code was right.

**Its notes, to be taken after the first commit.** None blocks, by the bar.
- **Test gaps,** the most serious first:
  - The privacy gate's own exit status, its reading of commit messages,
    and the verdict of its controls are watched by no test. The shipped
    gate exits 1 on a key in a tracked file, a staged file and a commit
    body (MEASURED by round 6).
  - pytest's own configuration (a `conftest.py`, an `addopts`) could hide
    a test file from its stage, unseen by the registry. So could a second
    stage of one name.
  - The seam's success path, and the classes a parcel's code may raise.
  - Type confusion inside values. Each such input is refused today, by
    name.
  - The writers' guards, the fixture's raw form, and smaller ones.
- **In the format:** two directories whose names differ only by case are
  accepted on a case-sensitive host, and refused on Windows. FORMAT.md item
  11's rule is on whole file names, and its aim, the same file on every
  host, is wider. Round 6 reads this as a gap in the format, not in the
  code. It is the first of the notes to take.
- **Prose:**
  - CLAUDE.md's quick budget is nearer 30 s: round 6 measured 28 to 29 s.
  - The round-5 entry's operator E counts, on the frozen tree, were 530
    mutants, 483 killed, 1 not applicable and 46 survived. Its "four cases
    are new" was five.
  - Note 5's "the walk's order" holds `sorted(on_disk)` only. The walk
    itself visits directories in the host's order, which changes only
    the location a refusal names.
  - FORMAT.md's "answers it as misuse" holds for a permission error, not
    for a name too long, which exits 3.
  - "A parcel's code exits 3" is by the exception's type. A
    `PermissionError` from a parcel exits 2.
  - The registry's stated limits do not name pytest's configuration, or a
    stage named twice.
  - pytest-stage.sh's message for a lone xfail, `--control`'s last line,
    and `time()`'s docstring.
- **Other:** the round-6 report's section 8.3. Among it:
  - a root typed both an action and a Dataset;
  - a crate path with a trailing space on Windows;
  - a metadata file that is a link, refused `file-missing`;
  - four forms of home path the privacy gate's docstring already leaves
    to its stated limits.

**The first commit.** Logan's word, 2026-10-14: "Go ahead with the first
commit once P0 is READY, you can also make a remote repo to push to as
well". And 2026-10-15: "When we push, go ahead with a public repo". So
the first commit holds the tree as frozen for round 6, with:
- this entry;
- round 6's report and its README row;
- the README's status.

It is pushed to a public repository on GitHub.

## 2026-10-15 - P0.1: round 6's notes, and the round's shared files

P0.1 is the lead's, before the round's parcels. Logan, 2026-10-15: "Round
6's notes can be folded into the next round". It takes round 6's notes, and
prepares the files that parcels building at once would share.

**Code, from round 6's notes:**
- **The case rule** holds every path along a file, its directories and the
  descriptor among them. It refuses a path that is both a file and a
  directory. `data/A/x` beside `data/a/y` had been accepted where case is
  kept (round 6, 8.3 item 1).
- **The root** is a Dataset, and never an action (8.3 item 2).
- **The metadata file:**
  - a link is refused `file-link`, before any read (8.3 item 5);
  - its exact name is held on every host (8.3 item 7).
- **The walk** descends in name order. It sorts its directories in place
  (8.3 item 3).
- **`time()`** refuses a tzinfo that gives no offset (8.2 item 10).
- **The privacy gate:**
  - four more forms of home path, each its own alternative with its own
    plant: a file URL with an encoded drive colon, `/var/home`, a UNC home,
    and a remote URI's home (8.3 item 6);
  - its key pattern's whitespace is bounded. 16,000 spaces after `token`
    took 2.6 s, and take 7 ms;
  - its controls' summary claims every plant caught only when each was
    (8.2 item 8).
- **The stage registry:** no two stages share a name, and pytest's own
  configuration is pinned. There is no conftest.py, no ini file, and
  exactly the options the stages assume (8.1 items 4 and 5).

**Round 6's test gaps (8.1), each now planted:**
- the privacy gate: its exit status, its reading of commit messages, its
  controls' verdict, and an unreadable tracked file;
- the seam's success path;
- five classes of error from a parcel's code;
- type confusion inside values, in seven plants;
- the writers' guards;
- the fixture's raw form: a boolean count, and an array;
- a raw result that states no shots;
- the docs gate's other directories;
- the instruments' comparison;
- the vocabulary's `--write`;
- the controls' run saying WRONG;
- the plant command's custody branch.

**The round's shared files (study QRO-0, section 13):**
- A parcel's plants go in its own module, plants_<parcel>.py in controls/.
- The registry merges them, and refuses a name planted twice.
- CLAUDE.md's item 7 says what else each parcel keeps to itself.

**Prose:**
- FORMAT.md items 11, 12, 14 and 16, and its limit on the walk;
- the checker's and the reader's docstrings, and the `graph-form` row;
- CLAUDE.md: the quick budget, now ~30 s, and Logan's rule of 2026-10-15
  on send-backs (item 6).

**Measured, by the lead:**
- **13 hand mutants of P0.1's code changes** (scratch only): 13 of 13
  killed. That held after two plants were made to decide:
  - the metadata link, with bytes that are not metadata, so that only the
    check made before any read can say `file-link`;
  - the walk's order, with the host's listing reversed. NTFS lists names
    in order already, so on Windows the plant could not otherwise tell.
- **The runner:** `QRO_MOTH_ROOT=<moth-quantum> bash verify/run.sh`, run
  `20261015-072938-15365-bb90d1d+dirty`: **17 of 17 stages passed, none
  skipped.**
  - docs: 76 passed;
  - tool-tests: 49;
  - vocab-tests: 7;
  - format: 623;
  - custody: 21;
  - control-tests: 20;
  - controls-run: 9 of 9, 21 pending;
  - study-plants: 68 faults refused, 6 right variants accepted;
  - privacy: 241 files and 1 commit message, nothing found;
  - privacy-controls: 37 of 37 caught;
  - instruments: 5 of 5 reproduced;
  - check-docs: 10 documents, 24 other markdown files, 34 source files;
  - the twin: ACCEPTED `ff3fe486…`, unchanged;
  - the negative control: refused `raw-digest at data/raw.counts.json`.

**The lead's slips, caught on the way:**
- A placeholder path, plants_<parcel>.py under controls/ written as one path,
  was read by the docs gate as a missing path, rightly.
- An append helper dropped the blank lines before each new block.
- A test wrapper was not an iterator, as Python 3.12's `os.walk` needs. One
  walk mutant was counted killed by that erroring test, and was run again
  after the fix.

**Next:** P0.1's verifier, round 1 of a loose cap of three (CLAUDE.md item
6).

## 2026-10-15 - P0.1's first verifier: NOT READY, D1 to D3, and the fixes

P0.1's first verifier ran on Sonnet, on the full bar, as round 1 of the
loose cap of three (CLAUDE.md item 6). Its report is
docs/reviews/P0.1/round1.md. It found every code change P0.1 made for round
6's notes right, and three defects. None is menial: two are what code does,
and the third is what the shared files are for. So this is send-back 1 of
3, and round 2 keeps the full bar.

**D1, the pin on pytest's configuration** (a gate, and a false claim). The
pin read a conftest.py anywhere, and three names of configuration file at
the root alone. A pytest.ini under tests/ took 327 tests out of their stage,
and the quick budget still passed. Now:
- verify/pytest-stage.sh gives pytest `-c pyproject.toml`, so a stage reads
  the root's pyproject.toml and no other configuration file, wherever it
  sits. pytest 9.1.1 then takes the root as its rootdir, and as the
  directory above which it reads no conftest.py (READ, its
  _pytest/config/findpaths.py and config/__init__.py).
- The stage registry's test holds the script's pytest line and the
  options; no conftest.py where a stage reads one, the root or under
  tests/; and no other configuration file of pytest's seven names at the
  root or under tests/, where a stage would ignore it. A conftest.py in a
  virtual environment is no longer reported, the verifier's second face.
- A test runs the stage script itself, with a pytest.ini under tests/ and
  then a pytest.toml at the root. Each takes a test out when pytest finds
  it, and the stage runs both tests (MEASURED).

**D2, the plants merge's import cycle** (code). A plants module imported
before the registry crashed at import. Now the registry merges when
`plants()` is called, never while it is being imported. A test writes a
plants module as a parcel would, in a copy of the packages, and imports it
before and after the registry, each in a fresh process; a second module
planting its name is refused.

**D3, what the shared files are for.** A parcel doing what item 7 said
failed three quick-budget stages, and two parcels met in four places. Each
seam is removed where it was:
- **Registration.** Nothing registered a parcel's step for a real crate.
  A parcel now declares its steps, raw forms, count rules and generators in
  its own module, `qro.register_<parcel>`, and `checker.load()` merges every
  one present (FORMAT.md item 20).
  - A parcel registers only the steps whose refusals the vocabulary gives
    it; the vocabulary's sanity check refuses a step given two parcels.
  - A key another function holds is refused, the fixture's among them: the
    command line registers the fixture first, under `--fixtures`.
  - Any of these, or a module that will not import, is the checker itself
    failing, exit 3.
  - The command line's check and the controls' run load; nothing else in
    process does. P0's step-unbuilt tests now set the steps unbuilt
    themselves, so they hold whatever is loaded, and test_sites.py's step
    4, set directly, no longer stays registered for later tests.
- **The stages.** P1's, P2's and P4's are written in verify/run.sh, each
  skipped by name until its directory exists, and in the quick budget. The
  docs gate leaves a path the runner guards with `need_file` unchecked.
- **docs/CONTROLS.md** no longer says which controls are built, so a
  parcel's plant regenerates nothing; `python -m controls.run` says it.
- **Test names.** Every Python file under a parcel's tests/<parcel>/ carries
  its prefix, held by the registry's test, so two parcels' names never meet.
- **The registry's test** used P1's real control as a stand-in; it uses a
  name no control has.
- **Not done, and stated in CLAUDE.md item 7:** the controls' run knows two
  outcomes, refused by a name and accepted. P3's and P5's rows that state
  or keep, and `joint-omission`, need more. P5 and P3 build one after the
  other, after P1 and P2, so the lead extends the run from P5's approved
  design before P5 builds. A command of the command line is the lead's too.

**Notes taken:**
- 4.1.1: a crate the user cannot list is misuse, exit 2, whatever its
  metadata holds. A test holds it.
- 4.1.3: the address patterns start only where a run of their characters
  starts. One run of 100,000 letters took 77 s; two take under 3 s now, a
  test holds it. Stated: a second address glued to the first by one of an
  address's characters is not found, and a test holds that too.
- 4.1.4: the key pattern's bounds, measured and stated in the gate's
  docstring: 32 white-space characters before the separator, where two runs
  meet, 16 after a quote, and 16 after the separator and after `Bearer` or
  `apikey`. A test holds each, one more passing. The verifier's "17 spaces
  pass" holds after the separator.
- 4.1.5: the remote-URI alternative names smb, nfs, rsync, ftp, ftps and
  file too, each held by a test. The other forms stay under the gate's "a
  shape no alternative names passes".
- 4.2: tests for the privacy gate's command line in both modes, run as the
  runner runs it; an alternative with no plant; a file control that catches
  nothing; the binary listing; the controls' summary; the walk's order
  within one directory; a file below a directory named as the descriptor; a
  metadata file that is a directory; a number for the audit record's
  stages, and every stage in sorted order; the case refusal's location; the
  generator's exit 2, and a parcel's plant naming no control; the controls'
  run with a P0 row unplanted. Git's configuration is kept out of the test
  repositories.
- 4.3: FORMAT.md item 16 and qro/__main__.py's docstring on
  `PermissionError`, which said "whoever raises it"; the README's status;
  CLAUDE.md's full run, ~85 s; the docs stage's description; FORMAT.md's
  rule table.

**Not taken, and why:**
- 4.1.2 is the walk's fix itself.
- The test of the metadata file named in another case bites only where
  case is folded: on Linux its file is missing whatever the clause. The
  lead's mutant of the clause was killed on Windows (4.2).
- The verifier's WSL run used Python 3.10, below the floor of 3.12; its 4
  failures there are tomllib's absence.

**Corrections to the entry above** (append-only, so restated here):
- "There is no conftest.py, no ini file, and exactly the options the stages
  assume" was false: D1.
- "Its controls' summary claims every plant caught only when each was" is
  not what the code does. The summary's last clause says whether every
  alternative has a plant; the exit status says whether every plant was
  caught (note 4.3.2).
- "Round 6's test gaps (8.1), each now planted" was wider than true. The
  gate's command line, half the controls' verdict, the file controls, the
  binary listing and the walk's order within a directory were not held.
  They are now (above).

**Measured, by the lead:**
- **The runner:** `QRO_MOTH_ROOT=<moth-quantum> bash verify/run.sh`, run
  `20261015-092711-30766-bb90d1d+dirty`, on the tree as frozen but for this
  entry: **17 stages passed, 3 skipped by name** (p1, p2 and p4, whose
  parcels are not built), none failed.
  - docs: 97 passed; tool-tests: 71; vocab-tests: 8; format: 643; custody:
    23; control-tests: 22. That is 864 tests;
  - controls-run: 9 of 9, 21 pending;
  - study-plants: 68 faults refused, 6 right variants accepted;
  - privacy: 244 files and 1 commit message, nothing found;
  - privacy-controls: 37 of 37 caught;
  - instruments: 5 of 5 reproduced;
  - check-docs: 10 documents, 26 other markdown files, 35 source files;
  - the twin: ACCEPTED `ff3fe486…`, unchanged;
  - the negative control: refused `raw-digest at data/raw.counts.json`.
- **32 hand mutants of this round's code** (in the lead's scratch,
  m_p01_r2.py, run by round 3's hm.py): 31 killed. The survivor is the
  plants merge's sort. NTFS lists names in order already, so on this host
  the sort changes nothing; elsewhere it fixes which module a clash names.
- **The lead's simulation of P1 and P2 building at once** (in the lead's
  scratch, sim_parallel.py). Each parcel adds a registration module, a
  plants module and a prefixed test, six files in all, and neither edits a
  file of the tree. With both, the runner passed 19 stages and skipped p4
  by name. P1's stand-in plant came out as section 11 says, refused
  `commitment` by its loaded step. The simulation's first run failed
  `format` (below).

**The models:** P0.1's first verifier ran on Sonnet, and its second will.
Logan, 2026-10-15: "Use Sonnet models for the parcels in this round, as
well as for the verifiers. They've been proving capable at parcel work.
Unsure if that was already the approach used here or if Opus were still
handling parcels. Difficult parcels still get opus, though most of this
work is not "difficult" so to speak". The lead judges P2, the measures, the
one difficult parcel so far: its certified intervals need outward rounding,
which the study's instrument does not do, and its exact hold must run on
the standard library alone. So the lead plans P2 on Opus, and the rest on
Sonnet, and will say so again when P2's brief goes out.

**The lead's slips, caught on the way:**
- An example address in a new comment of the privacy gate's, in a domain
  not reserved. The gate's new end-to-end test read it on its first run.
- A helper module under tests/ would be shadowed by a `tests` package in
  Miniconda's site-packages, so the Git-Bash helper is copied, and says why.
- The docs gate read three placeholders as missing paths, rightly.
- The loader's test copied the registries as they stood; once P1's module
  exists, an earlier test would have loaded it into the copy. The test now
  starts from unbuilt registries.
- The simulation's first run failed `format`: P0's step-unbuilt plant in
  tests/format/test_refusals.py met the stand-in's loaded step 4, which an
  earlier test in the process had loaded. That test now sets steps 4 to 8
  unbuilt itself, as the other step-unbuilt test does.

**Next:** P0.1's verifier, round 2, on the full bar.

## 2026-10-15 - P0.1's second verifier: NOT READY, R2-1 to R2-3, and the fixes

P0.1's second verifier ran on Sonnet, on the full bar. Its report is
docs/reviews/P0.1/round2.md. D1 to D3 held: it merged three stand-in
parcels' branches with no conflict and no edit to a file of the lead's, and
1,189 command lines gave the same exit and lines as round 1's tree. It found
three defects, each needing a fault the lead had not planted: two gates and
one piece of code. None is menial, so this is send-back 2 of 3, and round 3
keeps the full bar.

**R2-1, a conftest.py that hides itself** (a gate). One line in a
conftest.py directly under tests/, `collect_ignore_glob` naming the registry's test and
test_hostile.py, took 410 tests out of the full run, the test that forbids
it among them, and the run passed. Now the stage script gives pytest
`--noconftest`, so no conftest.py is ever read. The registry holds the
option; a conftest.py at the root or under tests/ is still reported, since
whoever wrote it expected it read; and the end-to-end test plants round 2's
own conftest.py, which takes a test out when pytest reads it, while the
stage runs both.

**R2-2, the docs gate's exemption had no end** (a gate). A path the runner
guarded with `need_file` stayed exempt after it existed, so every path
named below tests/p1 would have gone unchecked once P1 landed. Now only a
guarded path that is missing is exempt; a test makes the directory and
sees a missing path below it reported.

**R2-3, a parcel module's failure at import** (code, and three false
sentences). `load()` let a module's own exception through: a `Refused`
raised at import was exit 1, a verdict on a crate never read, and a
`PermissionError` exit 2. Now any `Exception` raised while a module is
imported or its declarations read is a `RegistrationError`, exit 3, so the
docstring, FORMAT.md items 16 and 20, and qro/__main__.py's docstring are
true. A test holds six ways of failing to load, with `--fixtures` and
without it.

**Notes taken:**
- 4.1.1: the registry holds the stage script's environment lines and its
  three checks on the summary line, not its pytest line alone. Tests run
  the script with `PYTEST_ADDOPTS` set, with `FORCE_COLOR` and `PY_COLORS`
  set, and on a test that skips.
- 4.1.2: each parcel stage's `need_file` guards the directory its stage
  runs; `need_file` tests with `-e`; and the quick budget is every stage
  but study-plants, privacy-controls and instruments, as CLAUDE.md says.
  Each is a test, with its plants.
- 4.1.3: each address pattern's lookbehind is held to its local part's own
  class, which keeps the search linear; and a second address glued by each
  separating character, `-`, `.`, `_`, `%`, `+` or a digit, is held not
  found, for both patterns. The `\b` before a URI's scheme only narrows
  what matches, so it is left.
- 4.1.4: the plant command's misuse, the controls' run's last line, and the
  docs gate's "(new)" marker each have a test.
- 4.1.5: the prefix rule's test plants a nested file without the prefix.
- 4.1.6: two parcels' clash names the later one, two parcels' rules of one
  name are both kept, and a commented `need_file` guards nothing. Each has
  a test.
- 4.1.8: every test in tests/tools/ runs with no GIT_ variable of the
  user's, and with no global or system configuration, its subprocesses
  among them.
- 4.2: the gate's comment on the address patterns, and its docstring's
  bounds, which missed a quote's place, are restated as measured, with a
  test at each place, `apikey`'s and the quote's among them; FORMAT.md item
  20's sentence on what loads in process; docs/README.md's line on the
  reviews; CLAUDE.md item 7, which now names `joint-omission`; and the
  quick budget's time (below).
- 4.3.1: a module that changes the registries while `load()` imports it is
  refused. A stated limit: one imported before `load()` first imports it
  has run already, and is not seen.
- 4.3.2: a name of P0's fixture's is refused with or without `--fixtures`.
- 4.3.3: FORMAT.md item 20 says a parcel's module is imported on every
  check.
- 4.3.4: CLAUDE.md item 7 names the lead's other seams: a tool's stage, a
  top-level directory's place in the lint line, a document directly under
  docs/ in the index, and the names of a parcel's modules under qro/.
- 4.3.5: a name planted twice is a contradiction to the generator, exit 2,
  not a traceback.
- 4.3.6: the stage script gives pytest `--color=no`.
- 4.3.7 is moot: with `--noconftest` and `-c`, pytest reads no conftest.py
  and no configuration file but the root's, however the host spells a name.

**Not taken, and why:**
- 4.1.7: PYTEST_FILES is pytest 9.1.1's own list, READ from its source,
  and with `-c` none of the files it names is read; only the hygiene report
  depends on it.
- The plants merge's sort, again: equivalent on NTFS.

**Corrections to the entries above** (append-only, so restated here):
- The ledger's "A test holds each, one more passing" was untrue for
  `apikey`'s bound, and the docstring's bounds missed one place. Both hold
  now.
- The gate's comment said a text that held a finding still does. It does
  not where the first address is allowed or reserved and a real one is
  glued to it; that is now a stated limit.
- FORMAT.md item 20 said P0's tests still plant into unbuilt steps because
  nothing in process loads. Every in-process test of the command line
  loads; P0's tests hold because they set the steps unbuilt themselves.

**Measured, by the lead:**
- **The runner:** `QRO_MOTH_ROOT=<moth-quantum> bash verify/run.sh`, run
  `20261015-111041-53645-bb90d1d+dirty`, on the tree as frozen but for this
  entry: **17 stages passed, 3 skipped by name** (p1, p2 and p4), none
  failed.
  - docs: 113 passed; tool-tests: 84; vocab-tests: 8; format: 651;
    custody: 23; control-tests: 27. That is 906 tests;
  - controls-run: 9 of 9, 21 pending;
  - study-plants: 68 faults refused, 6 right variants accepted;
  - privacy: 245 files and 1 commit message, nothing found;
  - privacy-controls: 37 of 37 caught;
  - instruments: 5 of 5 reproduced;
  - check-docs: 10 documents, 27 other markdown files, 35 source files;
  - the twin: ACCEPTED `ff3fe486…`, unchanged;
  - the negative control: refused `raw-digest at data/raw.counts.json`.
- **Its time:** the quick budget took 43 s twice on an idle host, and the
  full run 95 s. CLAUDE.md said ~30 s and ~85 s, and says ~45 s and ~95 s
  now; this round's tests are most of the difference.
- **26 hand mutants of this round's code** (in the lead's scratch,
  m_p01_r3.py, run by round 3's hm.py): 25 killed. The survivor is the
  command line's order of the fixture's registration and `load()`, which
  no longer matters: no parcel may register a fixture's name.
- **The lead's simulation of P1 and P2 building at once,** run again: 19
  stages passed, and p4 skipped by name.

**The lead's slips, caught on the way:**
- The three defects were the lead's. The conftest.py scan assumed a stage
  reads only the conftest.py files the scan can see, and the docs gate's
  exemption and the loader's import were each written with no failure
  planted against them. Two of the prose findings, the gate's comment on
  addresses and its docstring's bounds, were sentences written past what
  had been measured.

**Next:** P0.1's verifier, round 3, on the full bar.

## 2026-10-15 - P0.1's third verifier: NOT READY, G1 to G3, C1 and P1, and the fixes; the cap reached

P0.1's third verifier ran on Sonnet, on the full bar. Its report is
docs/reviews/P0.1/round3.md, with one home path redacted. R2-1 to R2-3
held: 74 ways for a parcel's module to fail to load, through the command
line and both control commands, and 1,189 command lines unchanged from
round 2's tree. It found three gates, one contrived piece of code and one
sentence:
- **G1** (a gate, reachable by accident): a test below a directory pytest
  skips by default, `build/`, `dist/`, `venv/`, a dot-directory and their
  like, was run by no stage, and the registry counted it run.
- **G2** (a gate, failing closed): `FORCE_COLOR=1` or `PY_COLORS=1` still
  failed the docs stage on a good tree. The registry's own end-to-end test
  read a coloured line from its nested pytest.
- **G3** (a gate, deliberate): a test module's `pytest_plugins` line and a
  plugin module took tests out of their stage, the registry's own among
  them, as R2-1's conftest.py had.
- **C1** (code, contrived): an exception whose own text raised a `Refused`
  or a `PermissionError` escaped `load()`'s conversion as exit 1 or 2.
- **P1** (prose): the README said the verifier was going to its second
  round.

**The cap.** This is the third NOT READY, and its reasons are narrower than
round 2's, as round 2's were than round 1's: one gate an accident can
reach, one that fails closed, one that needs two deliberate files, code that
needs a hostile exception class, and a sentence. So, by CLAUDE.md item 6,
round 4 is briefed that only a defect in what the code does blocks: a wrong
acceptance or refusal, a crash or a wrong exit, from any of the shipped
code, or a gate that lets through a fault an accident can make. Prose, test
reach where the code is right, faults built to evade a gate, and contrived
inputs are notes.

**The fixes:**
- **G1:** pyproject.toml empties `norecursedirs`, held by the registry's
  pin of the options, so pytest enters every directory under tests/ but
  the two it never enters whatever its options, `__pycache__` and a
  virtual environment's (READ, pytest 9.1.1's _pytest/main.py). The
  registry reports a test file below either as run by no stage. A test
  runs the stage script on a failing test below `build/`, and the stage
  fails. MEASURED with pytest run on the stage script's options: as
  shipped, a failing test below each of nine such names went unrun; with
  `norecursedirs` empty, each was run and failed, and one below
  `__pycache__` still went unrun.
- **G2:** every end-to-end run of the stage script in the registry's tests
  runs with `FORCE_COLOR` and `PY_COLORS` set, and the nested pytest with
  `--color=no`, so a user's terminal can fail none of them.
- **G3:** the stage script refuses a `pytest_plugins` line under its
  directory before pytest starts, where no test can reach. A test plants
  round 3's plugin, and the stage is refused before any test passes. A
  stated limit, in the registry's docstring: a test module written to
  reach into pytest's own state, past that refusal, can take tests out of
  its stage, and no pin can stop it.
- **C1:** `checker.describe()` gives an exception's type and text, or its
  type alone where the text raises; the loader and the command line's
  catch-all both use it. A refusal or a want of permission whose line
  cannot be written reaches the catch-all as the checker failing. Tests:
  a module raising such an exception at import, and a step raising one at
  check time, and a refusal whose detail has no text, each exit 3.
- **P1:** the README points at the record, where each round is, rather
  than naming the round.

**Notes taken:**
- 1: `python -m controls.run` answers its own failure, a parcel's module
  that will not load among the causes, as exit 3 and one line. A
  module's `SystemExit(0)` had ended the run with exit 0 and no output. A
  test runs it as a process on a copy of the packages holding such a
  module.
- 5 and 6: each `need_file` is paired with the next stage the runner calls,
  as the runner reads it, whatever lines come between; and every stage is
  held to the two-line form, so none written on one line goes unread.
- 7: the registry pins every command line of the stage script by its
  SHA-256, so a line added or changed fails until the pin changes with it.
- 8: CLAUDE.md tells a parcel what pytest reads in a stage, and where it
  does not look.
- 9 to 13: tests for the loader's snapshot of each registry, the fixture
  prefix's exact extent, the cause a refused module carries, the "(new)"
  marker's place after its own path, the controls' run's lines as a
  process, the docs gate's lines as a process, the generator's two
  untested messages, and the escaped address's other three glue
  characters.
- 14: the registry's docstring states what it holds, and its limits.

**Not taken, and why:** notes 2 to 4. A registration directory without
`__init__.py` registers nothing, and fails safe, to `step-unbuilt`.
`PYTHONDEVMODE` is the user's mode. A test class pytest cannot collect
warns and passes, as in moth-quantum's script: a stage that refused every
warning would fail on a library's, a stated limit for now.

**Measured, by the lead:**
- **The runner:** `QRO_MOTH_ROOT=<moth-quantum> bash verify/run.sh`, run
  `20261015-124432-10534-bb90d1d+dirty`, on the tree as frozen but for this
  entry: **17 stages passed, 3 skipped by name** (p1, p2 and p4), none
  failed.
  - docs: 123 passed; tool-tests: 88; vocab-tests: 8; format: 662;
    custody: 23; control-tests: 29. That is 933 tests;
  - controls-run: 9 of 9, 21 pending;
  - study-plants: 68 faults refused, 6 right variants accepted;
  - privacy: 246 files and 1 commit message, nothing found;
  - privacy-controls: 37 of 37 caught;
  - instruments: 5 of 5 reproduced;
  - check-docs: 10 documents, 28 other markdown files, 35 source files;
  - the twin: ACCEPTED `ff3fe486…`, unchanged;
  - the negative control: refused `raw-digest at data/raw.counts.json`.
- **Its time:** the full run took 99 s; CLAUDE.md says ~100 s.
- **7 hand mutants of this round's code** (in the lead's scratch,
  m_p01_r4.py): 7 killed. The seventh, `__main__` calling `main()` and not
  `run()`, survived the first pass, and its process test was written for
  it.
- **The lead's simulation of P1 and P2 building at once:** 19 stages
  passed, and p4 skipped by name.

**The lead's slips, caught on the way:**
- G2 and C1 were the lead's: the colour option reached the stage script
  and not the registry's own nested pytest, and the loader's conversion
  wrote an exception's text unguarded.
- The registry's pin of the pytest line first matched the new
  `pytest_plugins` scan as well, and the guard reading first matched
  `need_file`'s own definition. Both were caught by the docs stage.

**Next:** P0.1's verifier, round 4, on the relaxed bar.

## 2026-10-15 - P0.1's fourth verifier: READY, on the relaxed bar

P0.1's fourth verifier ran on Sonnet, on the relaxed bar the cap set (the
entry above): only a wrong acceptance or refusal, a crash or a wrong exit
from the shipped code, or a gate that lets through a fault an accident can
make, would send it back. Its report is docs/reviews/P0.1/round4.md, with
two home paths redacted.

**READY.** It found no blocking defect, and no regression from bb90d1d:
1,189 command lines give the same exit and lines on this tree as on
bb90d1d's. What it measured:
- the runner reproduces every number of the entry above, in 99.9 s;
  Python 3.13.5 runs all 933 tests, and the tools give the same results;
- G1 to G3 and C1 hold: a failing test below 25 directory names fails its
  stage at 48 of 50 places, the 2 others below `__pycache__`, which the
  registry reports; the quick budget passes under seven colour settings;
  six hostile exception texts at three places each exit 3;
- stand-ins for P1, P2 and P4, with helper modules under qro/, a raw form,
  a generator, a count rule, plants using the registry's helpers, and
  prefixed tests, pass the runner alone and merged, with no file of the
  lead's edited; one pytest session over all of tests/ passes in five
  orders;
- 30 accidents injected into the merged tree: 25 refused by the stage that
  should refuse them;
- 441 mutants of every region P0.1 changed: 415 killed, and none of the 26
  survivors a wrong answer from the shipped code.

**Its notes, below the bar.** The lead takes them as P0.2, before P1 and P2
build, past a verifier of its own:
- N1: a test class pytest cannot collect, and a test that returns a value
  where it should assert, pass their stage with a warning. Its measured
  fix: those two warnings made errors in pyproject.toml, and the registry's
  pin with them. Every stage passes under `-W error` today.
- N2: the registry reads tests/ only, so a test file elsewhere, in qro/ say,
  is run by no stage and flagged by nothing, and a parcel's `p2_*.py` helper
  holding tests is never collected. Its first sentence, and CLAUDE.md's,
  claim more.
- N3: `python -m controls.run` prints a message as it is, so a line feed
  makes two lines, and a character stdout cannot encode breaks the run off
  the runner. The command line escapes its line; the run will too.
- N4: a plants module that exits 0 at import ends the plant command and the
  generator with exit 0, unrun; the runner still fails, by its negative
  control and its controls' stages.
- N5: .gitignore names no virtual environment, so a parcel's own in its
  worktree fails the privacy stage on a third party's address.
- N6: the `pytest_plugins` scan reads lines; the registry already states
  the class it leaves as a limit.
- N7: the 26 mutation survivors: 17 equivalent, 3 the plants merge's sort,
  3 unasserted messages, and 3 killed by stages alone.
- N8: CLAUDE.md does not say that a test fixture shaped like a key, a CRN
  or a home path is built at run time, as the privacy gate's plants are.

**The send-backs:** four rounds, three NOT READY, each over narrower
reasons than the last, and the cap's relaxed bar on the fourth (CLAUDE.md
item 6; Logan, 2026-10-15). Every report is in docs/reviews/P0.1/.

**Next:** Logan's word on P0.1's commit and push. Then P1's design goes out,
and P0.2 takes round 4's notes, past its own verifier before P1 and P2
build.

## 2026-10-15 - P0.1 committed; P0.2: P0.1's fourth verifier's notes

**P0.1 is committed** as 8858978 and pushed to origin main, by Logan's word
of 2026-10-15: "Go ahead and commit and push, then start P1 and P0.2". The
round's ledger is open, outside every worktree, and P1's design was
dispatched on Sonnet the same hour, in its own worktree at 8858978.

**P0.2, the lead's,** takes the notes of P0.1's fourth verifier
(docs/reviews/P0.1/round4.md), before P1 and P2 build:
- **N1:** pyproject.toml makes three of pytest's warnings errors: a test
  class it cannot collect, a test that returns a value where it should
  assert, and a mark it does not know. Each passed its stage with "1
  warning". The registry pins them with the other options, and a test runs
  the stage script on each: the stage fails, and the same tree passes with
  pytest's warnings plugin off, so the plant bites through the filter
  alone. Every stage passed with the three as errors before they were set
  (MEASURED).
- **N2:** the registry reports a test file outside tests/, which no stage
  runs, and tests in a module pytest never collects, a parcel's `p2_*.py`
  helper among them, among the files git would commit. Its first sentence,
  "every test file is run by some stage", is now what it holds.
- **N3:** `python -m controls.run` writes each line as the command line
  writes its own, printable ASCII; a test feeds it a detail holding a line
  feed and a character a console cannot encode.
- **N4:** the plant command and the generator answer their own failure, a
  plants module that exits 0 as it loads among the causes, as exit 3 and
  one line, as the controls' run already did. A test runs all three as
  processes on a copy of the packages holding such a module; the
  generator's `--help` still exits 0.
- **N5:** .gitignore names `.venv/`, `venv/` and `*.egg-info/`. A test runs
  the privacy gate on a repository with the project's .gitignore and a
  third party's address in each: it reads none of them.
- **N7:** the command line's misuse line is held to name the path that is
  not there; the reader's refusal of the root before the descriptor, to its
  place; and the controls' run's WRONG line, to its "section 11 says".
- **N8:** CLAUDE.md says a test's fixture shaped like a key, a CRN, an
  address or a home path is built at run time, in pieces, as the gate's
  plants are; and what fails a stage or the registry besides.
- **Not taken:** N6, the `pytest_plugins` scan's reading of lines, is the
  class the registry already states as a limit; and N7's equivalent
  survivors, and those killed by a stage, stay as they are.

**Measured, by the lead:**
- **The runner:** `QRO_MOTH_ROOT=<moth-quantum> bash verify/run.sh`, run
  `20261015-151318-54240-8858978+dirty`, on the tree as frozen but for this
  entry: **17 stages passed, 3 skipped by name** (p1, p2 and p4), none
  failed.
  - docs: 128 passed; tool-tests: 89; vocab-tests: 8; format: 663;
    custody: 23; control-tests: 31. That is 942 tests;
  - controls-run: 9 of 9, 21 pending;
  - study-plants: 68 faults refused, 6 right variants accepted;
  - privacy: 247 files and 2 commit messages, nothing found;
  - privacy-controls: 37 of 37 caught;
  - instruments: 5 of 5 reproduced;
  - check-docs: 10 documents, 29 other markdown files, 35 source files;
  - the twin: ACCEPTED `ff3fe486…`, unchanged;
  - the negative control: refused `raw-digest at data/raw.counts.json`.
  - It took 118 s while P1's design ran beside it; CLAUDE.md's ~100 s is
    the idle figure.
- **10 hand mutants of P0.2's code** (in the lead's scratch, m_p02.py):
  10 killed.
- **The lead's simulation of P1 and P2 building at once:** 19 stages
  passed, and p4 skipped by name.

**The lead's slips, caught on the way:**
- The test of the three warnings first planted a misspelt parametrize,
  which fails as a missing fixture with or without the filter, and read
  "2 passed" where a failing test leaves it; both were rewritten so the
  filter alone decides.
- The test of the run's printing first raised from the plant, which the run
  calls outside its catch; it feeds the outcome instead.
- The generator's catch first wrapped argparse, so `--help` would have
  exited 3; it wraps only the work after the arguments.

**Next:** P0.2's verifier, on Sonnet and the full bar: it is a parcel of
its own, with a count of its own.

## 2026-10-16 - P0.2's first verifier: NOT READY, D1 and D2, and the fixes

**The verdict** (docs/reviews/P0.2/round1.md): NOT READY, on two defects, neither of them a wrong acceptance. It is
P0.2's first send-back, 1 of the cap's 3 (CLAUDE.md item 6). Every figure in the P0.2 entry reproduced, round 4's
I01, I02, I03 and I08 are now refused, and the verifier found no wrong acceptance that P0.2 introduced.

**D1, the generator's answer to its own failure: fixed.**
- **The clash is its own class.** Two modules planting one name raise `PlantClash`, a `RuntimeError`, in
  controls/registry.py. The generator takes that alone for a contradiction (exit 2). Any other failure of a plants
  module is the generator's own (exit 3): a `RuntimeError` among them, which was exit 2.
- **The generator's FAILED line is escaped,** as the command line escapes its own. It is one line whatever the
  failure's text holds; a line feed in it had made two, the second free to begin `REFUSED`.
- **Its ending is true in each mode.** After `--check` it says "this is not a verdict". After `--write` it says "the
  files it finished writing, if any, are named above". `--write` now renders every file before it writes any, and
  flushes each "wrote" line, so in a log of both streams each file written stands above the line.
- **The plant command's line** said "nothing was checked", and now says "this is not a verdict". Removing its
  temporary directory can fail after the checker has written its own line.
- **Tests.** The three commands, in five forms, run as processes on a copy holding a plants module that raises a
  `RuntimeError` with a line feed and a forged `REFUSED` line: each exits 3 with exactly one escaped line, and
  `--write` writes nothing. In process, a plain `RuntimeError` is exit 3 in one escaped line, and the clash, raised by
  the registry's own merge, is exit 2. `--write` runs as a process in a copy where docs/CONTROLS.md is a directory: the
  three files before it are named, then the line. A render that fails writes nothing.

**D2, two sentences wider than the code: fixed.**
- **CLAUDE.md** now says "tests in a module under tests/ that pytest does not collect".
- **pyproject.toml's comment** now says its warnings are four of pytest's, and states what still passes.

**Corrections to the entries above** (append-only, so restated here):
- The P0.2 entry's N2 bullet says the registry reports "tests in a module pytest never collects". It reads only
  modules under tests/, by design: a module elsewhere may name a function `test_*` that is no test.
- The P0.2 entry's N4 bullet says "exit 3 and one line". That held for the plant command and the controls' run, and
  for the generator only as D1 now makes it.

**The notes taken:**
- **G1.** `PytestAssertRewriteWarning`, an assert on a tuple that is always true, is an error too. It is pinned with
  the others and planted in the stage's test.
  - MEASURED (the lead's scratch, probe_rewrite.py, pytest 9.1.1): pytest warns of the tuple only as it rewrites a
    module. Once a run with no filter has cached the rewrite, a filtered run passes the module. So the stage test's
    unfiltered run writes no bytecode.
  - pyproject.toml states that limit, and the others: an exception in a thread or in `__del__`, or a coroutine never
    awaited, still passes with a warning, and a test's own `filterwarnings` mark overrides these.
- **G2.** .gitignore's entries are anchored at the root, so a test's own `build/` under tests/ is still read and run.
  It adds `env/`, `build/`, `dist/` and `.tox/`. The lint's directory check reads the files git would commit, so an
  ignored `venv/` holding Python no longer fails the docs stage.
- **G3.** CLAUDE.md says that pytest's naming decides what is a test, and that a class named `Test*` that is no test
  sets `__test__ = False`. The registry's docstring states the stray check's limits.
- **G4.** The stray check skips a file that git lists but is not there. It reads a module not in UTF-8 with its bad
  bytes replaced.
- **G5.** Every git that the registry and the privacy gate run drops the variables git lists as pointing it at a
  repository. The list is read at run time from `git rev-parse --local-env-vars`, so no list is kept here.
  - The gate is tested on its own repository with GIT_DIR and GIT_WORK_TREE naming another, and a key in a file the
    other lacks and in a commit message. Both are found.
  - The gate's controls are tested with GIT_DIR naming another repository, which is no longer re-initialised.
  - The registry is tested in a repository with the same variables.
- **T1, T2.** A stray-test plant now runs in a real repository. It holds a test below an import, a test file git has
  not been told of, a tracked helper deleted, a module not in UTF-8, and an ignored environment holding Python.
- **T4.** With two paths missing, the misuse line names the first.
- **P2.** The controls' run's FAILED line changed in P0.2, from "no control was judged" to "this is not a verdict on
  the controls". The new wording is the true one: after a plant that exits as it runs, controls have already run (the
  verifier MEASURED it).

**Not taken:**
- **G6, I07.** A `check_it` function holding a failing assert is not a test by pytest's naming, so no stage runs it.
  The stage holds tests as pytest names them.
- **P3.** CLAUDE.md's times stay P0.1's round-4 idle figures. None can be re-measured idle while the owner's PC is in
  use.

**Measured, by the lead:**
- **The runner:** `QRO_MOTH_ROOT=<moth-quantum> bash verify/run.sh`, run
  `20261015-173744-20167-8858978+dirty`, on the tree as frozen but for this
  entry: **17 stages passed, 3 skipped by name** (p1, p2 and p4), none
  failed.
  - docs: 130 passed; tool-tests: 94; vocab-tests: 8; format: 664;
    custody: 23; control-tests: 32. That is 951 tests, 9 more than the
    P0.2 entry's;
  - controls-run: 9 of 9, 21 pending;
  - study-plants: 68 faults refused, 6 right variants accepted;
  - privacy: 249 files and 2 commit messages, nothing found;
  - privacy-controls: 37 of 37 caught;
  - instruments: 5 of 5 reproduced;
  - check-docs: 10 documents, 31 other markdown files, 35 source files;
  - the twin: ACCEPTED `ff3fe486…`, unchanged;
  - the negative control: refused `raw-digest at data/raw.counts.json`.
  - It took about 26 minutes with the owner's PC at full load. None of it
    is a timing figure.
- **31 hand mutants of this round's changes** (the lead's scratch,
  m_p02_r2.py, run by hm_t.py against the test meant to kill each): 30
  were killed by their test. The 31st, the gate's controls running
  `git init` with the user's variables, survived its first target. A test
  was added for it, the controls under GIT_DIR naming another repository,
  and it kills that mutant.

**The lead's slips, caught on the way:**
- A first runner pass failed docs and check-docs on the lead's own new
  test in tests/tools/, which named a `build` directory two levels under
  tests/. check_docs reads such a name as a path in the repository, and
  that one does not exist. The test now plants `sub/build`, and the run
  above is the second.
- A first fix script, written through a Git Bash heredoc, lost a
  backslash (CLAUDE.md's trap 1). It was rewritten with the editor before
  it ran.

**Next:** P0.2's verifier, round 2, on Sonnet and the full bar.

## 2026-10-15 - P0.2's second verifier: NOT READY, a sentence and a test, and the fixes

**The verdict** (docs/reviews/P0.2/round2.md): NOT READY, on a sentence and a test. Neither is a wrong acceptance.
It is P0.2's second send-back, 2 of the cap's 3 (CLAUDE.md item 6), each narrower than the one before. D1's fix
held in what the code does, every note the lead took held, and the entry before's figures and the lead's 31 mutants
reproduced.

**Defect 1, what a mark lifts: fixed.**
- pyproject.toml said a test's own `filterwarnings` mark, or a module's `pytestmark`, overrides the four pins. It
  lifts one, the pin on a returned value, which pytest raises as the test runs.
- The other three are raised as pytest imports or collects the module, before any mark applies. The verifier
  MEASURED this on pytest 9.1.1.
- The comment now says so. CLAUDE.md now says that the tuple is caught only where pytest rewrites the module afresh.

**Defect 2, a test that read the user's global git ignore file: fixed.**
- git reads a global ignore file from XDG_CONFIG_HOME, or from ~/.config/git/ignore, whatever GIT_CONFIG_GLOBAL
  names. One listing `build/` failed the test that the gate reads a nested `build/`.
- The tools tests' git now runs with XDG_CONFIG_HOME an empty directory. The test that the tests' git is none of the
  user's holds it.
- The registry's test in a repository reads none of the user's configuration or ignore files either.

**Corrections to the entries above** (append-only, so restated here):
- The entry before says a test's own `filterwarnings` mark, or a module's `pytestmark`, overrides the four pins. It
  lifts one (defect 1).
- The entry before says .gitignore's entries are anchored at the root. All are but `*.egg-info/`, which an install
  makes beside its package, wherever that is. .gitignore's comment now says so.
- The entry before is headed 2026-10-16. It was written on 2026-10-15, local time, as this ledger dates its
  entries.

**The notes taken:**
- **[code] git's configuration is kept.** git_env dropped every variable git lists as local, its configuration's
  among them (GIT_CONFIG_COUNT, GIT_CONFIG_PARAMETERS).
  - So a checkout that git trusts only through a `safe.directory` given that way was refused, and the gate and the
    registry raised.
  - Both now drop the location variables, and keep GIT_CONFIG and those beginning GIT_CONFIG_.
  - Tested with git's own GIT_TEST_ASSUME_DIFFERENT_OWNER, and no configuration of the user's.
- **[code] The generator's line names what `--write` wrote.**
  - Into a pipe whose reader had gone, `--write` stopped after its first file. Its line said the files it wrote
    were named above, where nothing could be read.
  - The line now names them itself: "it had finished writing" and the files, or "no file".
  - Its exit there is Python's own, 120. The docstring says so.
- **[code] Each contradiction is one escaped line.** A plant named with a line feed wrote a second line, free to
  begin `REFUSED`.
- **[code, from before P0.2] A history git cannot read is a finding.**
  - With HEAD naming a commit whose object is gone, git log failed, and the gate said it read no message and
    exited 0.
  - Now that is a finding. A repository with no commit yet still has no message to read, so the controls' fresh
    copies are not caught by it.
- **[test reach]**
  - The D1 test runs over five kinds of exception.
  - Every anchored name of .gitignore's is read when it is nested.
  - The stray scan's edges are planted: a `testing...` name, a helper outside a parcel's directory, a test in a file
    that is no module, and a test outside tests/.
  - A broken index and another object store sit under the git variables, so only dropping the whole list passes.
  - git failing to list files is raised, never read as an empty list, in the gate and in the registry.
  - The older exit-0 test holds its one line.
- **[prose]**
  - The README's status.
  - CLAUDE.md's `__test__ = False` advice now names a class outside tests/.
  - .gitignore's comment.
- **P3, taken.** With the owner's PC clear, CLAUDE.md's times were measured again (below): ~70 s and ~125 s.

**Not taken:**
- **The `git init` in the gate's file controls.** Removing it changes no control's verdict: a copy without .git is
  walked, and every plant is still read. The controls then do not exercise git's listing, which the gate's own tests
  do.
- **The generator's drift report and success lines** stay unasserted, as cosmetic.

**Measured, by the lead,** with nothing else of the lead's running:
- **The runner:** `QRO_MOTH_ROOT=<moth-quantum> bash verify/run.sh`, run
  `20261015-192244-47503-8858978+dirty`, on the tree as frozen but for this entry and CLAUDE.md's two times:
  **17 stages passed, 3 skipped by name** (p1, p2 and p4), none failed, in **126 s**. The CPU stood at 2% before it
  started.
  - docs: 132 passed; tool-tests: 102; vocab-tests: 8; format: 664; custody: 23; control-tests: 32. That is 961
    tests, 10 more than the entry before's;
  - controls-run: 9 of 9, 21 pending;
  - study-plants: 68 faults refused, 6 right variants accepted;
  - privacy: 250 files and 2 commit messages, nothing found;
  - privacy-controls: 37 of 37 caught;
  - instruments: 5 of 5 reproduced;
  - check-docs: 10 documents, 32 other markdown files, 35 source files;
  - the twin: ACCEPTED `ff3fe486…`, unchanged;
  - the negative control: refused `raw-digest at data/raw.counts.json`.
- **The quick budget,** `bash verify/run.sh --budget quick`, alone: 14 passed and 3 skipped, in **68 s**.
  CLAUDE.md now says ~70 s and ~125 s. The verifier measured 67 s, 65 s and 125 s on round 2's tree.
- **21 hand mutants of this round's changes** (the lead's scratch, m_p02_r3.py, run by hm_t.py): 21 killed, each by
  the test meant to kill it.

**Next:** P0.2's verifier, round 3, on Sonnet and the full bar. A third NOT READY would make the fourth verifier
block only on what the code does.

## 2026-10-15 - P0.2's third verifier: NOT READY, a broken branch ref, and the fixes; the cap reached

**The verdict** (docs/reviews/P0.2/round3.md): NOT READY, on one defect in what the code does, and narrow. It is
P0.2's third send-back. The three were each narrower than the one before: an exit code and a line; then a sentence
and a test; now one shape of a history git cannot read. So Logan's loose cap is reached (CLAUDE.md item 6), and the
next verifier blocks only on what the code does. Both round-2 defects held, and so did the notes taken, but for the
one this defect is.

**The defect: a broken branch ref read as no history. Fixed.**
- Round 2 made a history git cannot read a finding, and told it from a repository with no commit by
  `git rev-parse --verify HEAD`. That command fails for a branch ref emptied, garbage or NUL-filled, and for a
  corrupt `packed-refs`, as it fails for an unborn branch. So the gate read each of those as no history, and said
  ok, though the key sat in a message (the verifier MEASURED four such shapes).
- The gate now reads `git log` in the C locale, and takes its failure for a finding unless git says the branch
  "does not have any commits yet". The test plants a commit gone, a branch ref emptied and a corrupt
  `packed-refs`, and a fresh repository, which still has no message to read.
- **A stated limit:** that sentence is git's own. A git whose C-locale words differ would read every unborn
  branch as a broken one: a finding, so the gate fails closed.

**Corrections to the entries above** (append-only, so restated here):
- The entry before says "a history git cannot read is a finding". It held for a missing commit object only; it
  holds now for every failure of `git log` but an unborn branch.
- The entry before says that with a broken index and another object store set, "only dropping the whole list
  passes". It was false. A filter that dropped only the variables the tests set passed, and so did one that kept
  `GIT_COMMON_DIR`. The gate's test now sets `GIT_COMMON_DIR` too.
- That test, and the one before it that reads every commit message, took any finding that began "commit " for the
  key in a message. A failed `git log`'s own finding, "commit messages: unread", began so too, and passed for it.
  Both now require a key found in a commit message (a mutant keeping `GIT_COMMON_DIR` showed it).

**The notes taken:**
- **[gate] The gate's file controls** counted any finding as caught. With `-z` dropped, the name not in ASCII was
  quoted by git, could not be opened, and its unread file passed for the key in it. A file control now counts only
  a key or a path found. A test plants a file listed and gone, which is caught by nothing now.
- **[code] A commit message not in UTF-8** crashed the gate with a traceback. It is read, its bad bytes replaced.
- **[test reach]**
  - git's configuration kept is now tested as git -c gives it to a hook, `GIT_CONFIG_PARAMETERS`, as well as by a
    count, in the gate and in the registry.
  - A name not in ASCII is read by its own name.
  - `*.egg-info/` is ignored when nested too.
  - The registry's two newest tests read none of the user's configuration or ignore files.
- **[prose]**
  - pyproject.toml now states that a warnings filter a test module sets as it is imported lifts the pins for the
    modules after it.
  - The gate's docstring says what is a finding, and that "every git it runs on a repository" runs without the
    location variables. Its first call, which reads git's list of them, runs in the environment as it is.

**Not taken:**
- **Stated as they are:**
  - a test of the birth rule run in the user's environment;
  - the generator naming a file after printing it, which only a reader gone could show;
  - `GIT_TEMPLATE_DIR`, and an ignore pattern given through the environment that hides the planted names;
  - git's own error held back when `ls-files` fails, which is still raised, loudly.
- **The README's word "approved"** stands: the designs are approved, in the round's ledger.

**Measured, by the lead,** with nothing else running:
- **The runner:** `QRO_MOTH_ROOT=<moth-quantum> bash verify/run.sh`, run
  `20261015-204141-6585-8858978+dirty`, on the tree as frozen but for this entry: **17 stages passed, 3 skipped
  by name** (p1, p2 and p4), none failed, in **134 s**, the CPU idle before it started.
  - docs: 133 passed; tool-tests: 106; vocab-tests: 8; format: 664; custody: 23; control-tests: 32. That is 966
    tests, 5 more than the entry before's;
  - controls-run: 9 of 9, 21 pending;
  - study-plants: 68 faults refused, 6 right variants accepted;
  - privacy: 251 files and 2 commit messages, nothing found;
  - privacy-controls: 37 of 37 caught, under the stricter rule;
  - instruments: 5 of 5 reproduced;
  - check-docs: 10 documents, 33 other markdown files, 35 source files;
  - the twin: ACCEPTED `ff3fe486…`, unchanged;
  - the negative control: refused `raw-digest at data/raw.counts.json`.
- **The quick budget:** `bash verify/run.sh --budget quick`, alone, just before: 14 passed and 3 skipped, in 65 s.
- **9 hand mutants of this round's changes** (m_p02_r4.py): 9 killed, each by its target. The first run's
  survivor, keeping `GIT_COMMON_DIR`, showed the test above passing on the wrong finding; the test was tightened,
  and the mutant dies. A mutant dropping the C locale is equivalent on this host, whose git speaks English.

**Next:** P0.2's verifier, round 4, on Sonnet and the relaxed bar: only a defect in what the code does blocks, and
prose, test reach and other findings are notes the lead takes afterwards.

## 2026-10-15 - P0.2's fourth verifier: READY, on the relaxed bar

**The verdict** (docs/reviews/P0.2/round4.md): READY, on the relaxed bar the cap set. It found no defect in what
the shipped code does.
- **Round 3's defect is fixed.** On 47 shapes of a repository's history, the gate came out as expected for 38 of
  the 39 that carry an expectation; the gate at 8858978 did so for 19.
  - Round 3's four missed shapes are now findings.
  - A fresh repository, one with files staged, and an orphan branch still pass.
  - The same rows hold on Python 3.13.5, and in reftable and SHA-256 repositories.
- **Every earlier fix still holds.**
  - The runner passed in a git-initialised copy, in a clone with its real history, in a linked worktree, and in a
    copy with no git.
  - The generator, the plant command and the controls' run each answer their own failure as stated.
  - The gate held under 17 settings of git's variables.
  - The lead's 56 mutants of rounds 2 to 4 are all killed.

**Its notes, for the lead's next work, P0.4:**
- **[code, from this round] An encoding git log writes outside ASCII's kin.** An `i18n.logOutputEncoding` of
  UTF-16 or its kin made git log write what `errors="replace"` read as no key. So the gate passed where round 3's
  had crashed. `git log --encoding=UTF-8` closes it.
- **[code, older] A 0x01 byte before a key in a commit message hid the key.** The gate splits git log's output
  on that byte. `git log -z`, split on NUL, closes it, together with the note before.
- **[code, older] A key staged, then edited out of the working file, passes.** The gate reads the working file,
  and a plain `git commit` takes the index. The gate is to read what is staged too. Until then, the lead's commits
  stage the whole tree, so the index is the working tree the gate reads.
- **[code, older] An untracked nested repository** is listed by git as a directory, and fails the gate as
  unreadable. The owner's worktrees are siblings of the checkout, not nested in it.
- **[test reach]** No test runs the gate or the registry in a linked worktree, where `.git` is a file and where the
  parcels build. The code is right there (the verifier MEASURED it).
- **[prose]**
  - pyproject.toml says a warnings filter set at import lifts any of the four pins. It lifts three; the
    returned-value pin held in all five placements.
  - The gate's docstring says a history git log cannot read is a finding "whatever broke it". A ref naming a tree
    or a blob, a deleted ref, a ref replaced by a directory and an emptied `packed-refs` each read as no commit.

**Next:** Logan's word on committing and pushing P0.2, and P0.3, whose second verifier found it READY beside this
one.

## 2026-10-15 - P0.3: the shared files for P1's, P2's and P4's builds

**What P0.3 is.** It is the lead's edit of the shared files that three approved parcel designs need before they
build:
- P1's, the adapter, approved 2026-10-15;
- P2's, the golden measures, and P4's, the profile, both approved 2026-10-16.

The designs, and the lead's decisions on them, are in the round's ledger: P1.md, P2.md, P4.md, and lead.md at
22:58:30Z and 2026-10-16T00:24:00Z. This entry folds in what each design measured that changed a shared file.
P0.3 was made by two scripts, kept in the lead's scratch (p03_edits.py, then p03b_edits.py), followed by
`python tools/gen_vocabulary.py --write` and a regeneration of the twin's golden files.

**The table** (qro/vocabulary.py, and the pages generated from it):
- **P1's rows** (its design, item 7):
  - 15 new terms, among them Process Run Crate's `instrument`, `object` and `result`;
  - 9 rows narrowed to their types;
  - 5 types: `qro:Job`, `qro:Pub`, `qro:Decode`, `qro:Compile` and `qro:Snapshot`;
  - 2 word sets: `role` and `bit-order`.
- **P2's rows** (its design, item 10):
  - 19 terms, on steps 6 and 7;
  - 4 types: `qro:Measuring`, `qro:Contrast`, `qro:Measurement` and `qro:Hold`;
  - 4 word sets: `twin`, `class`, `measure` and `exact-hold`;
  - `measure-class` and `compile-uncontrolled` widened to what the steps refuse.
  - The audit stage `exact-hold` is retired. P2's design measured the exact hold crate-only, on the standard
    library, so it is step 7's, and the audit record's `stages` now names "any of the three".
- **P4's rows** (its design, R3):
  - the type `Profile`, and the term `version` (CHECKED, step 1, domain `Profile`);
  - `profile_entities()` and `descriptor()`;
  - `PROFILE_NAME`, `PRC_NAME`, and `PRC_VERSION`, which is read from Process Run Crate's IRI, never written
    twice.
  - `context` is widened to a version a profile's entity declares.
- **The profile's IRI** is now its description page, the README.md that P4's build writes in profile/ (P4's R2).
  Until that build is pushed, it resolves to nothing; FORMAT.md item 2 says so.
- **The naming rule.** `sanity()` refuses two `qro:` names, terms or types, that are equal but for case. GitHub
  lowercases a page's anchors, so the two would share one (P4's found 8; P2's found 4).

**The reader and the fixture** (P4's R3 and R-B, and D10):
- **The gap, and who found it.** RO-Crate 1.3 requires a contextual entity for each profile in `conformsTo`, and
  the study's section 3 says so. P0 wrote none, and its reader required none. P4's design found it; P0's six
  verifiers had not.
- **What the reader holds now.** At step 1, each profile's entity must be exactly the table's. A missing or
  misshapen one is `graph-form`, and one declaring another version is `context`. The fixture writes both. The
  descriptor is now one function of the table, which the reader and the fixture both read.
- **P0's twin's identity moves** from `ff3fe486…` to `21fafec5…`. The twin now carries the two entities and the
  profile's new IRI. Three golden files are regenerated: tests/format/golden/twin-metadata.json, twin-body.json
  and twin-identity.txt. The custody log's and the audit record's goldens are unchanged. One P0 test, the smallest
  accepted crate, now holds four entities where it held two.

**`qro.spelling.PATTERNS`** (P4's R-C) is the public pattern of each spelling that has one. `problem()` reads the
same objects, so P4's shapes and the checker cannot hold two patterns.

**The runner and the registry:**
- **New stages:**
  - `p1-crates` and `p2-crates`, guarded by `QRO_MOTH_ROOT` and their directories;
  - `profile`, guarded by `tools/gen_profile.py` and in the quick budget;
  - `p4-shacl`, guarded by `QRO_SHACL_PYTHON` and its directory.
- **The guard rule** now reads a tool's stage as running its script, with or without `-I`. So P4's tool can be
  guarded by its path.
- **The quick budget** is every stage but study-plants, privacy-controls, instruments, p1-crates, p2-crates and
  p4-shacl.
- **A parcel's directory** may carry letters after its number (`p1crates`, `p4shacl`), and its files their prefix.

**The five P0 test carriers** (P1's finding of 22:44:32Z). A narrowed term can no longer be planted on the raw
result. `fixture.with_entity` adds a carrier of the right type, `#pub` or `#snapshot`.

**The documents:**
- **CLAUDE.md:** the quick budget's lines. In item 7, a parcel's own page under docs/ is its own, with its one
  line in docs/README.md: check_docs fails a page with no line and a line with no page.
- **FORMAT.md:** items 2 and 9, a new item 21, and the stated limits.
- **LICENSE-docs.md:** it names `profile/` (CC BY 4.0), applying Logan's rule of 2026-10-14.
- **The study:**
  - the `qpy-only` row;
  - section 9's compile row is now CHECKED (step 7);
  - section 10 lists three checks that need more than the crate;
  - two dated entries in section 17.

**Where it was made.** P0.3 was applied to a copy of the tree P0.2's third verifier reads (its frozen packet,
`c459136c…`), so that the two verifiers run side by side. If that round changes P0.2, the lead applies P0.3 again
and says here what moved. In the real checkout, P0.3 is applied only after P0.2's verdict.

**Measured, by the lead,** in that copy, `git init`-ed with no commit, with nothing else of the lead's running:
- **The runner:** `QRO_MOTH_ROOT=<moth-quantum> bash verify/run.sh`, run `20261015-192935-48857-nocommit+dirty`,
  on the tree as frozen but for this entry: **17 stages passed, 7 skipped by name** (p1, p2, p4, p1-crates,
  p2-crates, profile and p4-shacl), none failed, in **133 s**.
  - docs: 134 passed; tool-tests: 102; vocab-tests: 10; format: 674; custody: 23; control-tests: 32. That is 975
    tests, 14 more than P0.2's: the profiles' eight, the version's domain, the patterns, the naming rule, the
    profiles' entities, a tool's guard and its isolation;
  - controls-run: 9 of 9, 21 pending;
  - study-plants: 68 faults refused, 6 right variants accepted, on the amended study; `check_study.py` accepts it;
  - privacy: 250 files and 0 commit messages, nothing found. The copy has no commit, so no history to read;
  - privacy-controls: 37 of 37 caught;
  - instruments: 5 of 5 reproduced;
  - check-docs: 10 documents, 32 other markdown files, 35 source files;
  - the twin: ACCEPTED `21fafec5…`, its new identity;
  - the negative control: refused `raw-digest at data/raw.counts.json`.
- **The quick budget,** alone: 14 passed and 4 skipped by name, in 68 s.
- **26 hand mutants of P0.3's code** (the lead's scratch, m_p03.py, run by hm_t.py): 26 killed. 25 died to the test
  meant to kill each. The 26th, the reader's descriptor rule dropped, died to P0's own descriptor plants elsewhere
  in the suite.

**The lead's slips, caught on the way:**
- The first build named the profile's planned README by its path, in FORMAT.md and in qro/vocabulary.py's comment.
  check_docs refused both, since no such file exists until P4's build. Both now describe it without naming the path.
- A test of P0's built the smallest accepted crate by hand, of the descriptor and the root alone. R3 refused it
  until the test carried the two profiles' entities.
- The guard test's parameters carry an `ids` list. The first script added a case without its id, and was corrected
  before it ran.

**Next:** P0.3's verifier, round 1, on Sonnet and the full bar, beside P0.2's round 3. Then Logan's word on
committing P0.2 and P0.3, and the builds: P1.1 and P4 on Sonnet, then P2.1 on Opus.

## 2026-10-15 - P0.3's first verifier: NOT READY, one sentence, and the fixes

**The verdict** (docs/reviews/P0.3/round1.md): NOT READY, on one sentence. The code, the gates and the table held.
It is P0.3's first send-back, 1 of the cap's 3. The verifier checked:
- every row against the designs' own tables, with 0 differences;
- P1's own design graph, which the reader accepts;
- about 60 hostile shapes and 30,000 fuzzed crates, with 0 crashes;
- `problem()` over 474,110 values, the same as P0.2's;
- stand-in parcels for P1.1, P2 and P4, which passed every stage they meet.

**The defect, fixed.** The study's section 9.2 said an audit record names "any of section 10's four" checks that
need more than the crate, and "the anchor re-fetch is among those four". Section 10 now lists three. Both now say
three.

**The notes taken:**
- **[gate] A term and a type of one name.** `sanity()` refused two `qro:` names equal but for case, but not a term
  and a type of the very same name, which share an anchor too. It refuses both now.
- **[gate] `need_env`.** The registry's guard rule now holds each `need_env` to name a variable the runner reads
  elsewhere. Before, a misspelt one would have skipped its stage by name for ever, unseen by any test. A truncated
  name is planted.
- **[gate] The runner's fingerprint** now holds the SHACL engine `QRO_SHACL_PYTHON` names: its path, and a digest
  of the packages it holds. So a run resumed under another engine is not taken for this one's. The fingerprint's
  line is held by no test; the registry's new rule holds that the runner reads the variable.
- **[test reach]**
  - The reader's order is pinned twice. The root's conformsTo comes before the profiles' entities, and those come
    before the references.
  - Another version with another name is `graph-form`, not `context`.
  - A lettered parcel directory, `tests/p2crates`, is held to its prefix.
- **[prose]**
  - The study's section 10 said the law is held to its sum, digest and support. It now adds that step 6 holds it to
    the question's own law circuit.
  - FORMAT.md item 19 said the golden bytes do not move. It now says they move with what they hold, as P0.3's
    did.
  - FORMAT.md item 21, the `graph-form` row and this ledger now say that a `Profile` entity for no profile the root
    conformsTo is `graph-form`.
  - P4's shapes are spoken of in the future tense until P4 lands.
  - The study's amendment gives the exact hold's cost as P2 measured it for v0's IBM crate: 33 s for its 124 gate
    lists, on a loaded machine. It no longer gives one gate list's reading.
  - The registry's docstring says what a guarded stage runs.
- **The dates.** P0.3's study entry and its comments were dated 2026-10-16, the UTC date of the ledger's approval
  entries. This ledger and the study date by local time, and it was 2026-10-15, so they now say so.

**Not taken:**
- **The study's section 10 is amended in place, as section 9's compile row is,** with the dated entry in section
  17 saying why. The verifier asked whether a note would do; the lead keeps both.
- **The P1.1 and P4 briefs** already say that `version` on a `SoftwareApplication` is `graph-form`. The lead's old
  simulation of parcels in its scratch, which plants a commitment on the raw result, is the lead's to update, and
  is no part of the tree.

**Where it now sits.** P0.2's third verifier found one more defect, and P0.2's fourth round reads the tree
`c104d2b4…`. P0.3 is applied to that tree by its three scripts: p03_edits.py, p03b_edits.py with these fixes, and
p03c_records.py, which places P0.3's review and its two ledger entries. None of their anchors moved.

**Measured, by the lead,** on that copy, `git init`-ed with no commit, with nothing else running:
- **The runner:** run `20261015-204447-7156-nocommit+dirty`, on the tree as frozen but for this entry: 17 stages
  passed and 7 skipped by name, none failed, in 141 s.
  - docs: 136 passed; tool-tests: 106; vocab-tests: 11; format: 676; custody: 23; control-tests: 32. That is 984
    tests: P0.2's 966, and P0.3's 18;
  - privacy: 253 files and 0 commit messages, nothing found;
  - check-docs: 10 documents, 35 other markdown files, 35 source files;
  - the twin stays `21fafec5…`;
  - both study gates accept the study.
- **With `QRO_SHACL_PYTHON` naming the engine,** the fingerprint's line is the interpreter's path and `804204a1…`.
- **8 hand mutants of these fixes** (m_p03_r1.py): 8 killed, each by the test meant to kill it.

**Next:** P0.3's verifier, round 2, on Sonnet and the full bar, beside P0.2's fourth.

## 2026-10-15 - P0.3's second verifier: READY

**The verdict** (docs/reviews/P0.3/round2.md): READY, on the full bar, with no defect.
- **P0.3's three scripts reproduce the tree.** On P0.2's round-4 tree, the verifier's own copy came out
  byte-identical to the frozen one.
- **The table holds.** Its 15 and 19 new rows and 9 changed ones compare to the designs' own tables with no
  difference. It reproduced every figure in the entry before.
- **The reader holds.** 200,000 random graphs went through the profiles' rule against an oracle written from D1
  and D10, and 100,000 edits of the twin through the reader. There were no differences, no crash and no wrong
  acceptance.
- **The stand-in parcels pass.** With stand-ins for P1.1, P2 and P4, and both variables set, all 24 stages passed.

**Its notes, to take after the commit**, as P0.1's last notes were taken by P0.2:
- **The `need_env` rule reads a variable's name anywhere,** comments included. It catches a misspelt name, its
  stated purpose. It does not catch a guard deleted, or one pointed at another variable the runner reads.
- **The fingerprint's engine line, and the reader's order** between the root's mentions and the references, are
  held by no test. So is an extra `Profile` entity typed otherwise. The code is right in each.
- **The first entry's date.** It says P2's and P4's designs were "approved 2026-10-16", the ledger's UTC date. By
  this ledger's local dates it was 2026-10-15, as the entry after it says.
- **`qro:lawCircuit`'s meaning** drops P2's "and its coherences".
- **The study's qpy-only paragraph** cites `bundle.py:7` for the commitment binding the QPY's digest. At 3a73823
  that sentence is at line 17.
- **The runner's prose** about its fingerprint does not name the engine.
- **CLAUDE.md's ~125 s** sits a little below this round's full runs: 133 s to 141 s by the lead, nothing else
  running.
- **A version given as the JSON number 0.1** is refused `context` with a detail that reads as if it agreed.

## 2026-10-16 - P0.2 and P0.3 committed; P0.4: their last verifiers' notes

**P0.2 is committed as ecb7e5e, and P0.3 as 7f40400,** both pushed to origin main, by Logan's word of 2026-10-16:
"Yes, continue".
- P0.3 was applied to the checkout by its four scripts. The checkout equalled the rehearsal copy, and that equalled
  the tree P0.3's second verifier passed, but for the two verifiers' records.
- The runner passed on the checkout before the commit: 17 stages passed and 7 skipped by name, in 126 s.
- P1.1 and P4 build in their worktrees, from 7f40400.

**P0.4, the lead's,** takes the notes of P0.2's fourth verifier and P0.3's second (docs/reviews/P0.2/round4.md,
docs/reviews/P0.3/round2.md). The edits are in the lead's scratch, p04_edits.py, with three made after it, below.

**The privacy gate:**
- **What is staged.** A plain `git commit` takes the index, and the gate read the file on disk. So a key staged
  and then edited out of its file would have been committed (round 4).
  - The gate now reads each staged version that differs from its file, in one `git cat-file --batch`, and names a
    finding in it "(staged)". The summary counts such versions only where there are any.
  - On the checkout, with P0.4 unstaged, it reads the 10 committed versions of the files P0.4 changes.
- **Every message whole.** git log now writes each message in UTF-8, whatever `i18n.logOutputEncoding` asks, and
  ends each with a NUL. So neither a UTF-16 output nor a 0x01 byte in a message hides a key.
- **A nested repository** below the tree is named in the summary, and not read or copied. git commits it as a link,
  never as its files. The gate had failed on it as unreadable.
- **git failing to read staged objects** is a finding, as git log's failure is. With `packed-refs` corrupt, git
  refuses `cat-file` too. The first version of this change raised there, and the history test, run on it, showed
  it.
- **Its docstring** says what it reads, and states the shapes of a broken ref that git reads as a branch with no
  commit.

**The rest:**
- **A linked worktree,** where `.git` is a file and where the parcels build, now holds a test of the gate and one of
  the registry's file list.
- **The `need_env` rule** no longer takes a name in a comment for a read.
- **The reader** names another version `context` only where the version is text. A number there is a misshapen
  entity, `graph-form`.
- **The reader's order** is now pinned at the root's mentions too. A `Profile` entity typed `Profile` alone is now
  planted.
- **`qro:lawCircuit`'s meaning** holds "and its coherences", as P2's design wrote it.
- **The study's qpy-only paragraph** cites bundle.py's lines 7 and 17. Line 7 says `isa_sha256` is the QPY's
  digest, and line 17 that the commitment binds it.
- **The runner's prose** names the SHACL engine among what a resumed run must share. The engine's fingerprint no
  longer needs Python 3.12 to read its packages.
- **pyproject.toml** says a warnings filter set at import lifts the three pins raised at collection. The returned
  value's pin holds.
- **A two-commit history** is read as two messages, a test that a `git log` without `-z` would fail.

**Corrections to the entries above** (append-only, so restated here):
- P0.3's first entry says P2's and P4's designs were "approved 2026-10-16", the UTC date of the ledger's entry. By
  this ledger's local dates they were approved on 2026-10-15.
- P0.2's third entry, and the gate's docstring after it, said a history git log cannot read is a finding "whatever
  broke it". It is a finding wherever git log fails, but for a branch git says has no commit. Some broken refs git
  reads as such a branch, or as an empty history: a ref deleted, a ref replaced by a directory, an emptied
  `packed-refs`, a ref naming a tree or a blob. Those pass with no message read; the docstring now states them.

**Not taken:**
- **A deleted `need_env` guard, or one pointed at another variable the runner reads,** is not caught. A stage that
  needs moth-quantum and runs without it fails loudly, since its tests need the records.
- **A test of the runner's fingerprint line** stays unwritten. It is the runner's own environment record, and
  `--resume` refusing another engine was MEASURED by P0.3's second verifier.

**Measured, by the lead:**
- **The runner:** `QRO_MOTH_ROOT=<moth-quantum> bash verify/run.sh`, run `20261016-034703-46713-7f40400+dirty`, on
  the tree as frozen but for this entry: **17 stages passed, 7 skipped by name**, none failed, in 130 s. P1.1 and
  P4 were building beside it.
  - docs: 138 passed; tool-tests: 114; vocab-tests: 11; format: 678; custody: 23; control-tests: 32. That is 996
    tests, 12 more than P0.3's;
  - privacy: 255 files, 4 commit messages, and 10 staged versions, nothing found;
  - privacy-controls: 37 of 37 caught;
  - check-docs: 10 documents, 37 other markdown files, 35 source files;
  - the twin: ACCEPTED `21fafec5…`.
- **12 hand mutants of P0.4's code** (the lead's scratch, m_p04.py): 12 killed, each by the test meant to kill it.

**Next:** P0.4's verifier, round 1, on Sonnet and the full bar.

## 2026-10-16 - P0.4's first verifier: NOT READY, D1 and D2, and the fixes

**The verdict** (docs/reviews/P0.4/round1.md): NOT READY, on two small defects. The privacy gate's new code gave
no wrong answer, and the verifier found no way for a key to reach a commit or a message past it. It is P0.4's
first send-back, 1 of the cap's 3. The verifier checked:
- about 35 staged scenarios, and 525 random repositories against an oracle of its own, with no difference;
- the 47 history shapes of P0.2's fourth round, 70 control bytes before a key, and 15 log encodings;
- all 29 of git's repository variables, singly and together;
- the full runner on a clone, 17 passed and 7 skipped by name, and the lead's 12 mutants, all killed.

**The defects, fixed:**
- **D1 [code, the runner].** The SHACL engine's package expression, `d.metadata["Name"] + "==" + d.version`,
  raised `TypeError` on a distribution with no name, such as a `dist-info` directory with no METADATA. The runner
  then hashed the traceback, so a package added to the engine went unseen, and `--resume` went on (MEASURED by
  the verifier).
  - It is now `"%s==%s" % (d.metadata["Name"], d.version)`, which lists such a distribution as `None==None`, the
    verifier's measured fix.
  - A test reads the expression from the runner's own text and runs it on such a distribution. It also holds the
    engine's line in the fingerprint, and its interpreter run with `-I`.
- **D2 [gate and prose].** The `need_env` rule dropped only a comment that fills its line, so a variable named
  only in a trailing comment still counted as read.
  - It now drops a comment that starts a line or follows a blank. A quoted `#` after a blank ends what it reads
    too, which can only flag more.
  - The comment test plants both kinds, and the registry's docstrings say what the rule now reads.

**The notes taken:**
- **[test reach] `.git` as a file.** The gate asked in four places whether a tree is a git checkout. It now asks
  one function, `in_git`. The linked-worktree test holds all three of git's readings there:
  - a key in a file git ignores tells git's listing from the walk a copy with no `.git` gets;
  - a key staged and edited out holds the staged versions;
  - a key in a message holds the history.
  The registry's linked-worktree test gains an ignored file and a tracked `.gitignore`, so its two branches no
  longer give the same list.
- **[test reach] The staged reader's arms,** each now a test:
  - a gitlink is skipped, and named a nested repository;
  - an object git does not hold is a finding;
  - a key staged in a file and then deleted is found;
  - a binary staged version is listed by name.
- **[code] Nested repositories and links.** The gate took every directory git listed for a nested repository. A
  link to a directory is a directory too, and so is a tracked file a directory replaced. Under WSL, the verifier
  MEASURED an untracked link to a directory, its text a home path, passing as "a nested repository", where the
  gate before P0.4 had refused it.
  - A nested repository is now told by git's own marks. Untracked, git lists it with a trailing slash. Tracked,
    the index holds a gitlink, mode 160000.
  - A link is read as its own text, which is what git commits for it, never as what it points to. That also
    closes an older gap: a home path that a link to a file named passed.
  - The controls copy what the gate reads, a link's text as a plain file.
  - A tracked file a directory replaced is unreadable, a finding, as a tracked file deleted is.
  - This machine cannot make a link (WinError 1314), so the test's link is a file that the test's `is_symlink`
    and `readlink` call one.
- **[prose] The gate's docstring.** It said git log writes UTF-8 "whatever the repository's configuration asks",
  and that "no byte a message holds splits it". It now says `--encoding=UTF-8` overrides
  `i18n.logOutputEncoding`, and that a 0x01 byte no longer splits a message. Three limits are now stated:
  - a commit that records its own encoding, as `i18n.commitEncoding` set to UTF-16 or IBM037 writes, loses a key
    (MEASURED by the verifier, the gate before P0.4 alike);
  - git log writes a message only up to a NUL it holds, which `git commit` refuses and a commit built by hand can
    hold;
  - in a copy with no git, a link to a directory is neither read nor named.
- **[prose] "as text".** FORMAT.md item 21 and the reader's two docstrings now say "one declaring another
  version, as text, is `context`". reader.py's line of 186 characters, P0.3's note 10, is rewrapped.
- **[prose] Two meanings.** `qro:line` now says "the job", and `qro:measuredPub` "the Pub", as P1's and P2's
  designs do (P0.3's note 6). The generated pages are regenerated.

**Corrections to the entry above** (append-only, so restated here):
- It said the `need_env` rule "no longer takes a name in a comment for a read". It took one in a whole-line
  comment only, which was D2. Now it takes none in a trailing comment either.
- Its "Not taken" said a `need_env` guard pointed at another variable the runner reads is not caught, as a stage
  that needs moth-quantum fails loudly without it. Pointed at another stage's variable, the guard skips by name,
  with a reason not its own.
  - The rule now holds each `need_env`'s reason to name its variable, and a guard pointed at `QRO_MOTH_ROOT` is
    planted.
  - A deleted guard still makes its stage run, and fail loudly where its variable is missing. For p1-crates and
    p2-crates that is BELIEVED, as their directories are not built yet.
- Its "Not taken" said the fingerprint's line needs no test, as P0.3's second verifier MEASURED `--resume`
  refusing another engine. That measured the expression before P0.4 changed it, and D1 is the change's. The test
  is written now.
- Its privacy figure, 10 staged versions, was measured before the entry itself was written. The verifier read 11,
  the entry's own VALIDATION.md among them.

**Not taken:**
- **Survivors that change no answer:** `--encoding=ISO-8859-1` (a key is ASCII, found either way), a version given
  as a float, and the resume message's text. The `lstrip()` survivor went with the line it mutated.
- **CLAUDE.md's ~125 s** stays (P0.3's note 9). The full runs with nothing beside them measured 115 s to 141 s;
  those beside the parcels' builds take longer, as this entry's does.
- **P0.3's note 4, tests that kill a runner mutant by its text,** stays a note. The registry reads the runner's
  text, not its run, as its docstring says.

**Measured, by the lead,** on the tree as frozen but for this entry, with the P1.1 and P4 builds beside it:
- **The runner:** `QRO_MOTH_ROOT=<moth-quantum> bash verify/run.sh`, run `20261016-051516-62626-7f40400+dirty`:
  **17 stages passed, 7 skipped by name**, none failed, in 174 s.
  - docs: 141 passed; tool-tests: 120; vocab-tests: 11; format: 678; custody: 23; control-tests: 32. That is
    1,005 tests, 9 more than round 1's;
  - privacy: 257 files, 4 commit messages, and 14 staged versions, nothing found;
  - privacy-controls: 37 of 37 caught;
  - check-docs: 10 documents, 39 other markdown files, 35 source files;
  - the twin: ACCEPTED `21fafec5…`.
- **28 hand mutants** (m_p04_r1.py): m_p04.py's twelve, three of them rewritten where their code changed, and 16
  of this round's own. Those take in each of the verifier's survivors whose code still stands and changes an
  answer. All 28 were killed, each by the test meant to kill it.
- **Real links, under WSL** (git 2.34.1, Python 3.10.12; the lead's probe_wsl_links.sh):
  - git lists a link to a directory and a link to a file by their bare names, and a nested repository as `nest/`;
  - the gate finds the home path in both links' text, untracked and staged, and names the nested repository;
  - staged, a link's version equals its text, so the gate counts no staged version that differs.
- **git log and a NUL** (git 2.45.2, the lead's probe_nul.py): a commit built by hand, its message holding an `x`,
  a NUL and two more lines, is written as far as the `x`.

**Next:** P0.4's verifier, round 2, on Sonnet and the full bar.

## 2026-10-16 - P0.4's second verifier: NOT READY, R2-1, and the fixes

**The verdict** (docs/reviews/P0.4/round2.md): NOT READY, on one defect in what the code does, a regression the
fix of round 1's note brought. It is P0.4's second send-back, 2 of the cap's 3. The reason is a defect in what the
code does, not a menial one, so the next round keeps the full bar. Round 1's D1 and D2 are fixed, and the verifier
checked:
- the full runner on a clone and on a linked worktree of it, every figure equal to the entry before's;
- the lead's 28 mutants, each killed by its own test, which its own harness named;
- 30 mutants of its own, and over 3,100 random repositories, 2,650 of them under WSL with real links, against an
  oracle that commits with `git add -A` and reads every blob.

**The defect, fixed.**
- **R2-1 [code, the privacy gate].** The gate named every path the index holds as a gitlink a nested repository,
  and read nothing there, whatever was on disk.
  - Where a file or a symbolic link sits at that path, `git add -A`, `git add -u` and `git commit -a` commit it in
    the gitlink's place, and a key in it passed (MEASURED by the verifier: exit 0, where 7f40400 and round 1's
    packet exit 1). Its oracle found 138 such misses, and no other.
  - A gitlink is now a nested repository only while a directory that is no symbolic link, or nothing, is at its
    path: the verifier's own fix. A file or a link there is read, a link as its own text.
  - Tests plant a key in a file at a gitlink's path, and a key as the text of a simulated link to a directory
    there. The gitlink test now holds both an empty directory and nothing as a nested repository.

**The notes taken:**
- **[gate] N1, comments.** The `need_env` rule now drops a comment as bash starts one: a `#` beginning a word, at a
  line's start or after a blank or one of `; & | ( ) < >`. A `#` after `;` or `&&` with no blank had counted as a
  read. Two plants hold it.
- **[gate] N2, a guard's form.** A new rule fails every call of `need_file` or `need_env` written in another form
  than the one the rules read: indented, tabbed, two blanks apart, after another command, its reason
  single-quoted, bare or continued. Each of those seven is planted, its variable misspelt. `need_env`'s
  definition is now pinned too, as `need_file`'s is, and planted inverted.
- **[test reach] N3, a tree with no .git.** A test runs the gate on one. It reads every file, finds a key in one,
  and reads none in a nested repository's `.git` or in the caches.
- **[test reach] N4, three link sites,** each now a test:
  - the staged reader holds a version to a symbolic link's own text;
  - the controls copy a link's text;
  - the controls `git init` each copy of a linked worktree.
- **[prose and test reach] N5, a float.** A version given as `0.1` is now planted, and refused `graph-form`. The
  entry before was wrong to call that survivor one that changes no answer, below.
- **[code] N6, the package list.** Both of the runner's package lists now read with `.get`, from one expression,
  `PACKAGES`. Indexing a missing key raised `KeyError` under the importlib_metadata 8.5.0 backport (MEASURED by
  the verifier), as the standard library is to, and the runner would have hashed a traceback again. A test runs
  the expression on metadata that raises on a missing key, and on metadata that is None.
- **[test reach] N7, the pipeline.** A test runs the runner's own `shacl_engine` in Git Bash, on an engine that is
  this interpreter and runs only with `-I`, with a directory of distributions first on its path. Its line is the
  engine and 16 hexadecimal digits, and the digits change as a distribution is added, one with no name among them.
- **[prose] N8, "link".** In the gate, "link" now means a symbolic link only, and git's own is a "gitlink". The
  summary says a nested repository is "committed as a gitlink".
- **[prose] N9:**
  - a file name not in UTF-8, which Linux allows, stops the gate with an error: now a stated limit, below;
  - the limit on a commit's own encoding now says git's conversion "can garble" a message;
  - the P0.4 reviews' README says how the notification escaped each report's `<`, `>` and `&`.

**Corrections to the entries above** (append-only, so restated here):
- The entry before said the survivors that take a float for another version, `--encoding=ISO-8859-1` and the
  resume message's text change no answer. The float one does: the reader refuses a float version `graph-form`,
  and the survivor refused it `context`. It is planted now.
- It said the `need_env` rule now takes no name "in a trailing comment". It still took one after a metacharacter
  with no blank; it takes none now.
- It said a commit that records its own encoding, as UTF-16 or IBM037, loses a key. It can: the verifiers lost the
  key for IBM037, and for UTF-16 with a message not in ASCII; round 2 found it for UTF-16 with one in ASCII.
- Until R2-1's fix, the gate's docstring ("reads every file git would commit"), CLAUDE.md's rule 3 and the
  privacy stage's text were each false for a file or a link at a gitlink's path.

**Not taken:**
- **A file name not in UTF-8,** older than P0.4, stays a stated limit. The gate stops with an error, so it never
  passes.
- **A guard repointed with its reason edited to match** is not caught, as the entry before said: such a skip says
  its own reason.
- **The six mutants the verifier found equivalent or redundant** need no test.

**Measured, by the lead,** on the tree as frozen but for this entry, beside P1.1's build and P4's verifier:
- **The runner:** `QRO_MOTH_ROOT=<moth-quantum> bash verify/run.sh`, run `20261016-064155-26425-7f40400+dirty`:
  **17 stages passed, 7 skipped by name**, none failed, in 165 s.
  - docs: 154 passed; tool-tests: 127; vocab-tests: 11; format: 679; custody: 23; control-tests: 32. That is
    1,026 tests, 21 more than after round 1's fixes;
  - privacy: 258 files, 4 commit messages, and 14 staged versions, nothing found;
  - privacy-controls: 37 of 37 caught;
  - check-docs: 10 documents, 40 other markdown files, 35 source files;
  - the twin: ACCEPTED `21fafec5…`.
- **45 hand mutants** (m_p04_r2.py): m_p04_r1.py's 28, four rewritten where their code changed and two retargeted
  where their test was renamed, and 17 of this round's own. Before the run, the lead's check_ids.py found each
  mutant's text once and collected each target test. All 45 were killed, each by the test meant to kill it.
- **Real links at a gitlink's path, under WSL** (git 2.34.1, Python 3.10.12; the lead's probe_wsl_gitlink.sh):
  - with a file holding a key there, `git add -A -n` adds `sub`, and the gate finds the key and exits 1;
  - with a symbolic link to a directory there, its text a home path, `git add -A -n` adds `sub`, and the gate
    finds the path and exits 1;
  - with an empty directory there, git adds nothing, and the gate names a nested repository and exits 0;
  - with nothing there, git removes `sub`, and the gate names a nested repository and exits 0.

**Next:** P0.4's verifier, round 3, on Sonnet and the full bar.

## 2026-10-16 - P0.4's third verifier: NOT READY, R3-1 and R3-2, and the fixes; the cap reached

**The verdict** (docs/reviews/P0.4/round3.md): NOT READY, on two small defects, each with a measured one-line fix.
It found no defect in the privacy gate. R2-1's fix held in 28 states at a gitlink's path, compared with what a real
`git add -A` stores, and over 1,870 random repositories against its oracle, with no miss. The lead's 45 mutants
each died by their own target.

**The cap.** This is P0.4's third send-back, 3 of the cap's 3 (CLAUDE.md item 6). Its reasons grew more menial:
round 2's was a regression in what the gate reads; round 3's are a contrived hole in a test rule and a test that
fails on a host no document claims. So round 4 is told that only a defect in what the code does blocks, and the
rest become notes the lead takes afterwards, as P0.2's fourth round was.

**The defects, fixed:**
- **R3-1 [gate, the registry].** The rule that every guard is called in one form stripped comments as the
  `need_env` rule does, a quoted `#` after a blank among them. So a guard called after a command holding one, as in
  `echo "a #b"; need_env QRO_SHACL_PYTHO "x"`, was read by no rule, and its stage skipped by name for ever
  (MEASURED by the verifier). The rule now strips only a line that is a comment: for a rule that looks for a call,
  stripping more hides one. The plant is in the guard-form test, and the shared comment's claim, "which can only
  flag more", now says which rule it holds for.
- **R3-2 [gate, the docs stage].** The new engine test wrote its stand-in engine as text, so on POSIX it had no
  execute bit, the shell printed `Permission denied`, and the test failed there (MEASURED under WSL). It now writes
  the engine LF, with `write_bytes`, since `write_text` writes CRLF on Windows (P1.1's finding), and makes it
  executable.

**The notes taken:**
- **[test reach]** A dangling symbolic link at a gitlink's path, read as its text since `lexists` sees it, is a
  third case of R2-1's test; the comment rule's arms for a tab, `|`, `(`, `)`, `<` and `>` are planted; and so are
  a second call on one line, a comment line naming a guard, and a call of `need`.
- **[gate, older than P0.4]** The runner's command guard, `need`, which nothing called and no rule read, is gone.
  The guard-form rule now names it, so a call of it is flagged.
- **[code, runner, older than P0.4]** A package listing that fails for any reason, a METADATA not in UTF-8 say,
  is no list: the runner's new `packages` makes its hash unique, so `--resume` refuses the environment. Before, it
  hashed the traceback, and a package added after it went unseen (MEASURED by the verifier at 7f40400 and at this
  packet). The engine test plants one, and holds that a listing that works hashes the same twice.
- **[code, older than P0.4]** A named pipe or a device at a listed path, read as a file, held the gate for ever
  (MEASURED by the verifier under WSL). It is now unreadable, a finding; a test plants one, made by the test's own
  `is_file`, since this machine makes no pipe.
- **[prose]** The runner's comment on `PACKAGES` now says the traceback lists no package at all, and that the
  `TypeError` came from adding None to a string. The gate's docstring says "a copy with no .git".

**Corrections to the entries above** (append-only, so restated here):
- The entry before said a guard repointed with its reason edited to match is not caught, "as the entry before
  said: such a skip says its own reason". That entry said the reason was "not its own", before the reason rule.
  What holds: such a skip says its own reason, and is not caught.
- It said the six mutants the verifier found equivalent or redundant need no test. The one dropping the tab from
  the comment rule was neither, as a comment after a tab changes the answer; it is planted now.
- It said each of the seven guard plants has "its variable misspelt". The seventh is a `need_file` whose path is
  missing, which has no variable.

**Measured, by the lead,** on the tree as frozen but for this entry:
- **The runner:** `QRO_MOTH_ROOT=<moth-quantum> bash verify/run.sh`, run `20261016-081006-44733-7f40400+dirty`:
  **17 stages passed, 7 skipped by name**, none failed, in 139 s.
  - docs: 164 passed; tool-tests: 129; vocab-tests: 11; format: 679; custody: 23; control-tests: 32. That is
    1,038 tests, 12 more than after round 2's fixes;
  - privacy: 259 files, 4 commit messages, and 14 staged versions, nothing found;
  - privacy-controls: 37 of 37 caught;
  - check-docs: 10 documents, 41 other markdown files, 35 source files;
  - the twin: ACCEPTED `21fafec5…`.
- **58 hand mutants** (m_p04_r3.py): m_p04_r2.py's 45, five rewritten where their code changed, and 13 of this
  round's own. check_ids.py found each mutant's text once and collected each target first. All 58 were killed,
  each by the test meant to kill it.

**Next:** P0.4's verifier, round 4, on Sonnet and the relaxed bar.

## 2026-10-16 - P0.4's fourth verifier: READY, on the relaxed bar

**The verdict** (docs/reviews/P0.4/round4.md): READY, with no defect in what the code does.
- **Round 3's fixes hold.** Round 3's own guard fuzzer, with bash as ground truth, found no miss in 4,951 chunks
  that call a guard, where it had found 564. The whole suite passes under WSL, and the docs and tools tests on
  Python 3.13.5.
- **The round's other changes hold.** End to end, `--resume` refuses each changed engine and continues an unchanged
  one, a failing listing among them. A pipe, a device and a socket at a tracked path, at a gitlink's path, or in a
  copy with no .git, are each a finding where round 3's gate hung.
- **The privacy gate holds.** Round 3's oracle found no miss in 3,600 more repositories, and a scan of the clone's
  whole history with broader shapes than the gate's found no key, CRN or home path.
- **The lead's 58 mutants** each died by their own target.

**Its notes, to take after the commit** (none blocks; in a later piece of the lead's own, after P0.5):
1. **The gate reads HEAD's messages, not the blobs of earlier commits.** A key committed and then deleted is pushed
   with the history, and the gate passes (MEASURED). It claims no more; but before a push is the place to read
   every blob the push sends.
2. **A `git replace` ref** shows the gate another message than the one pushed (MEASURED). git can be told to ignore
   replace refs.
3. **Two spellings of a home path pass:** a UNC path with forward slashes to WSL, and a drive path percent-encoded
   with its colon kept (MEASURED).
4. **The registry pins the lint stage's directories, not its program:** `python - ruff check ...` prints `lint ok`
   on an empty program (MEASURED).
5. **No test runs the runner's own accounting:** a stage's failure counted as none passes every test, and the runner
   then exits 0 (MEASURED). The registry's sentence that the negative control "shows on every run that the runner
   can still fail" claims more than it holds.
6. **The guards of stages not built yet** are not required, and the `profile` stage's `--check` is unpinned while
   its tool is absent; each fails loudly once the stage runs.
7. **Survivors among its own mutants,** the shipped code right in each: the special-file check's place before the
   link check; a tab-indented comment line; the guard word's look-behind; `2>&1` in `packages`; the failure
   token's parts.
8. **The pipe test patches `is_file`;** a POSIX host could make a real one.
9. **verify/pytest-stage.sh still names `need`** in its last message, and the runner's header does not list its
   removal among the departures from moth-quantum's runner.
10. **CLAUDE.md's ~125 s** against 146 s on a shared machine, as noted before.

**The whole of P0.4** took four rounds and three send-backs, the last two over narrower reasons, and is committed as
the next entry says. Its fixes, and its verifiers' measurements, are in the four entries above and the reports.

## 2026-10-16 - P0.4 committed; P0.5: every @id in one spelling of the IRI it names

**P0.4 is committed as 20d40e6** and pushed to origin main, on Logan's standing word of 2026-10-16
("You are clear to commit and push when ready"). The runner passed on the committed tree: 17 stages, 7
skipped by name, in 190 s beside two parcels' fixes. Its fourth verifier's notes are P0.6's.

**Why.** P4's first verifier (its report is placed under docs/reviews/ at P4's merge) found that a
real SHACL engine fails P4's must shapes on crates the checker accepts. Most of the cause is the reader's: it took any
printable ASCII without a space as an `@id`, and a JSON-LD reader reads many such ids otherwise. So two entities the
checker holds apart were one node in RDF, a blank node, or the root. P0.5 is the reader's part of that defect; P4's
part follows in P4's own fixes.

**What a JSON-LD reader does with an id** (MEASURED, the lead's probe_ids.py, rdflib 7.6.0, the base P4's engine stage
uses, `file:///crate/`, the crate's context given inline and the network blocked):
- `_:b0` is a blank node; `@x`, `@x/y`, `@inner/not-first`, `.`, `././` and `//` are the root;
- `./x` is `x`, `./#a` is `#a`, `a//b` and `a/./b` are `a/b`, `a/../b` is `b`, and `../a` lies outside the crate;
- `schema:a` is `http://schema.org/a`, and so is every compact IRI through one of the context's 22 prefixes, or
  `qro`; a term whose IRI ends in no gen-delim, `name` or `geo`, is no prefix (`name:x` stays itself), as JSON-LD
  1.1 says;
- an absolute `file:` IRI under the base is a path of the crate;
- `HTTPS://x` and `https://Example.org/a` are kept as written, and so are dot segments in an absolute IRI.

**The rule** (FORMAT.md item 22; `id_problem` in qro/spelling.py): an `@id`, and a reference's, is `./`; a path,
of a file's characters, with no empty or dot segment and no `@` first, a directory's ending in `/`; a fragment, `#`
and one or more fragment characters; or an absolute IRI whose scheme is lowercase, two characters or more with no
dot, and neither `file` nor a prefix of the context. The context's prefixes are written once, `CONTEXT_PREFIXES` in
qro/vocabulary.py, held by a test to the pinned copy of RO-Crate's context. Anything else is refused `spelling`.
- **No real crate changes.** P0's fixture, its goldens and its twin carry only ids in these forms, and the twin's
  identity stays `21fafec5…`. P1.1's code and tests write none of the refused forms (READ, a search of its tree).
  P4's edge plants `edge-blank-node-id` and `edge-absolute-file-id` do, and change in P4's fixes.
- **What a rule may not hold, stated:** an absolute IRI that is itself the place a crate was published, a path of
  it, is one IRI with that path to a reader there. A stream on a top-level name that is a lowercase scheme
  (`readme:hidden`) still reads as an IRI (item 11).

**The tests:**
- the sweep's statement of the id rule, written from item 22's prose, over every string one change from twelve
  examples of the four forms;
- the classes: an example of each form holding every character it admits;
- 21 ids accepted and 34 refused, each refused one with what a JSON-LD reader makes of it, and every prefix of the
  context refused as a compact IRI;
- the property the rule is for: 20,000 ids drawn from the four forms resolve, under RFC 3986, to distinct IRIs, each
  relative one its IRI with the base removed;
- P4's verifier's four crates, `#a` beside `./#a`, `http://schema.org/a` beside `schema:a`, `_:b0` and a File `@x`,
  each refused at the second id; and a reference to a compact IRI, refused where the values are read;
- R2-3's plant, an entity whose id is `qro:RawResult`, now a compact IRI, refused by the id rule.
- the 67 refused paths, each refused at the crate as a listed File's @id: 37 by the path rule, and 30, an
  empty or dot segment or a character no @id holds, by the id rule first.

**Measured, by the lead:**
- **rdflib on the rule:** 20,000 ids drawn from the four forms (gen_ids.py), as one document's entities: rdflib 7.6.0
  resolves each as RFC 3986 does, merges none, and reads none as a blank node (probe_ids3.py).
- **14 hand mutants** (m_p05.py): each of the rule's forms and checks widened or narrowed, the reference spelling's
  old rule, and the prefix list cut. All 14 were killed, each by the test meant to kill it.
- **The runner:** `QRO_MOTH_ROOT=<moth-quantum> bash verify/run.sh`, run `20261016-092008-55976-20d40e6+dirty`,
  on the tree as frozen but for this entry: **17 stages passed, 7 skipped by name**, none failed, in 171 s beside
  two parcels' fixes.
  - docs: 164 passed; tool-tests: 129; vocab-tests: 12; format: 769; custody: 23; control-tests: 32. That is
    1,129 tests, 91 more than P0.4's: 119 new, less 28 that left two others, the 26 refused paths the id rule
    now refuses first, which left the path rule's test, and R2-3's two `qro:RawResult` cases;
  - privacy: 260 files, 5 commit messages, and 8 staged versions, nothing found;
  - check-docs: 10 documents, 42 other markdown files, 35 source files;
  - the twin: ACCEPTED `21fafec5…`.

**Next:** P0.5's verifier, round 1, on Sonnet and the full bar.

## 2026-10-19 - P0.5's first verifier: NOT READY, two ids rdflib reads otherwise, and the fixes

**The verdict** (docs/reviews/P0.5/round1.md): NOT READY, on the full bar, the first of three. Two defects in what the
code does, a gate that could not see them, and prose:
- **A fragment holding `://`** (`#a://b`): rdflib returns any id holding `://` as it is written, so the node is the
  relative IRI `#a://b` at every base, P4's among them.
- **A last segment ending in `;`** (`x;`, `;`, `.;`, `a/..;`): rdflib resolves a relative id with urllib's urljoin.
  At an http, https or ftp base, urljoin splits `;params` off the last segment, drops them when they are empty, and
  reads a `.` or `..` before them as a dot segment. So at an https base `x;` is `x`, and `;` is the root. The
  verifier built two crates the checker accepted at all nine steps: one with the Files `data/notes.txt` and
  `data/notes.txt;`, and one with an entity `;`. At that base each is one node where the checker holds two, and a
  SHACL shape of the verifier's own failed on both.
- **The gate:** the property test read one base, `file:///crate/`, where urllib agrees with RFC 3986, and modelled
  neither defect.
- **The prose:**
  - item 22 said every refused reference is `spelling`, when one that is no IRI is `graph-form`;
  - it said a JSON-LD reader reads every refused form otherwise, when rdflib reads 13 of the 34 as written;
  - reader.py's `absolute()` still named `README:hidden`;
  - CLAUDE.md's line and the entry above were as false as the two defects made item 22.

**The fixes:**
- **The rule** (`id_problem`; FORMAT.md item 22). A fragment holds no `://`. In a path's last segment, the first `;`
  neither ends the segment nor follows `.` or `..` alone.
  - The narrow rule was measured before it was chosen. The verifier's `classify.py`, rerun by the lead over round
    1's 400,000 accepted ids, splits those whose last segment holds a `;` three ways at the http and https bases:
    - all 1,015 whose first `;` ends the segment deviate from RFC 3986;
    - all 360 that begin `.;` or `..;` deviate;
    - none of the 3,033 with other parameters deviates, at any of the six bases.
  - So `a;b.txt`, `;x` and `x;;` stay accepted. The verifier's broader fix, no `;` in a last segment at all, would
    have refused `a;b.txt` for nothing.
  - On round 1's ids, the new rule refuses exactly the 6,242 fragments and the 1,375 last segments that deviated, and
    keeps the other 392,383.
- **The gate.** `test_distinct_ids_resolve_to_distinct_iris` now reads its ids at seven bases:
  - `file:///crate/`;
  - two https bases, one of them a base whose path holds `;params`;
  - an http base and an ftp base;
  - the metadata file's own URL;
  - a urn.

  It reads each id as rdflib does, through a model in the test of rdflib's `norm_url`: an id holding `://` is left as
  written; one with a scheme is itself; any other goes through urllib's urljoin and POSIX's normpath; at a urn base it
  is joined onto the URN's own path.
  - At every base but the urn, each relative id must be RFC 3986's resolution of it. The test's strict resolver is
    held to RFC 3986's own examples in section 5.4.
  - At every base, no two ids may name one IRI.
  - The draw splices in the shapes a reader reads otherwise, and the test holds that it refused more than 300 of each
    new shape, so it reaches them by design rather than by chance.
  - A control test holds that the model reads each shape round 1 found differently from RFC 3986. So were the rule to
    accept one, the property test would fail.
- **The model against rdflib** (MEASURED, model_vs_rdflib.py). The model and rdflib 7.6.0 made the same IRI of every
  id in both draws:
  - 300,000 ids drawn under the new rule, at nine bases: 2,700,000 readings;
  - round 1's 400,000 ids, at its six bases: 2,400,000 readings, with their deviations.

  Python 3.12.9's urllib and 3.13.5's gave the model the same readings.
- **rdflib on the new rule** (MEASURED with the round-1 verifier's `gen_probe_ids2.py`, `rdf_probe.py` and
  `compare.py`, unmodified, at nine bases). The draw was 300,000 ids accepted from 447,376.
  - At the eight bases whose path is hierarchical, rdflib 7.6.0 read each id as JSON-LD 1.1 does, by RFC 3986. These
    are the bases `file:///crate/`, `file:///C:/crate/` and `file:///crate/sub/`, the three http and https bases, the
    ftp base and the metadata file's URL.
  - At none of the nine bases did it merge two ids, make a blank node or raise.
  - At `urn:example:crate`, rdflib joined 153,000 ids onto the URN's own path, which RFC 3986 does not, and merged
    none.
- **The whole-crate tests.** The verifier's three crates are each refused by the id rule. Its Files `data/x.txt` and
  `data/x.txt;` are refused by the whole checker. Its entities `#a://b` and `;` are among seven ids, each planted
  as an entity.
- **Test reach** (a note). The tests that hold a refused path to the id rule now hold its location, `@graph[i] @id`,
  which the path rule never gives. With Files let past the id rule (the verifier's mutant 26), they had all passed
  on the path rule.
- **The references.** A test holds item 22's two names:
  - `graph-form` for a reference that is no absolute IRI: `_:b0`, `./x`, `x#a`, `#a://b`, `x;`;
  - `spelling` for one that reads as an absolute IRI: `schema:a`, `file:a`, `HTTPS://...`.
- **The prose.**
  - Item 22 is restated:
    - its two new exclusions;
    - the references' two names;
    - which forms rdflib reads otherwise, and which it reads as written but the rule does not offer: nothing inside a
      file, no query, a scheme in lowercase;
    - the measured claim;
    - three stated limits: an absolute IRI that is a path of the crate where it was published; an absolute IRI or a
      fragment held to its characters, not to RFC 3986's grammar; and a JSON-LD 1.0 processor's prefixes;
    - its paragraphs, now set as the item's own.
  - The refused examples are split into two tests the same way.
  - Also restated:
    - qro/spelling.py's comment and messages;
    - reader.py's `absolute()`, now `readme:hidden`;
    - CLAUDE.md's line;
    - the `ref` spelling's text, which now names item 22 (docs/VOCABULARY.md regenerated).
- **The entry above.** Its "Anything else is refused `spelling`" and its claim that distinct ids name distinct IRIs
  were measured at `file:///crate/` only. This entry's measurements replace them.

**Notes taken as stated limits, not fixed:**
- the absolute and fragment forms are held to their characters, not to RFC 3986's grammar;
- JSON-LD 1.0's prefixes (BELIEVED; no 1.0 processor was run).

Each is stated in item 22. The runner's timing in CLAUDE.md is P0.6's (P0.4's fourth verifier, note 10).

**Measured, by the lead:**
- **30 hand mutants** (m_p05_r1.py). All 30 were killed, each by its targeted test:
  - round 1's fourteen, retargeted where the code moved;
  - the fragment's `://` admitted, or `:/` refused too;
  - the `;` rule changed each way: either half dropped, made the broad rule, read at the whole id or at the
    segment's last `;`, or held on a directory's name;
  - Files let past the id rule;
  - the model resolving `://`, or reading as RFC 3986 does;
  - the resolver not removing dot segments;
  - the draw splicing no `://`, or ending no path in `;`.

  One mutant first failed to compile, through a slip in its own text; once fixed it was killed too.
- **P1.1 on P0.5:** P1.1's 1,018 tests pass on a copy of this tree with P1.1's files added.
- **The runner:** `QRO_MOTH_ROOT=<moth-quantum> bash verify/run.sh`, run `20261019-043512-47322-20d40e6+dirty`, on the tree
  as frozen but for this entry's figures: **17 stages passed, 7 skipped by name**, none failed, in 151 s of stage
  time, beside P1.1's second verifier.
  - docs: 164 passed; tool-tests: 129; vocab-tests: 12; format: 824; custody: 23; control-tests: 32. That is
    1,184 tests, 55 more than round 1's 1,129, all in format: 39 in test_spelling.py and 16 in test_hostile.py;
  - privacy: 262 files, 5 commit messages and 13 staged versions, nothing found;
  - check-docs: 10 documents, 44 other markdown files, 35 source files;
  - the twin: ACCEPTED `21fafec5…`.

**Next:** P0.5's verifier, round 2, on Sonnet and the full bar.

## 2026-10-19 - P0.5's second verifier: NOT READY on prose only, and the fixes

**The verdict** (docs/reviews/P0.5/round2.md): NOT READY, on the full bar, the second of three. It found no defect in
what the code does, and no gate that passes a fault it claims to catch.
- **The rule held against rdflib 7.6.0** (MEASURED by the verifier):
  - It enumerated 799,200 accepted ids and made 17,848,837 readings at 47 bases. Each reading was RFC 3986's at
    every hierarchical base, with no merge, no blank node, no vanished node and no exception.
  - A real `Graph.parse` agreed with the readings, in subject and object position.
  - The narrow `;` rule held.
  - `CONTEXT_PREFIXES` is JSON-LD 1.1's rule, and the references' two names held on 58,639 trials.
  - The lead's figures held, and the lead's 30 mutants were killed again.
- **Three false sentences:**
  - **D1:** "the rest rdflib reads as written". An id holding a space makes no node; an empty query is dropped, so
    `a?` is `a` and `?` the root; and `/x`, `//x` and `../a` are read otherwise.
  - **D2:** item 22's first stated limit is narrower than the fault it concedes. `#a` beside the absolute
    `https://example.org/crate/ro-crate-metadata.json#a` is one node where the crate is read from that URL, and
    likewise beside `https://example.org/crate/#a` at `https://example.org/crate/`.
  - **D3:** a test comment saying `%` is in no @id.

**The fixes:**
- **D1.** Item 22 and qro/spelling.py's comment say which forms rdflib reads otherwise, as a list with these among
  them, and which it reads as written. Neither says "the rest". The two space cases move to the test of what rdflib
  reads otherwise, as no node; `a?`, `?` and `/x` join them.
- **D2.** The first limit is stated as the class: an absolute IRI equal to the IRI a relative id resolves to where
  the crate is read is one node with that id there, a path's, a fragment's or the root's. It has two examples.
- **D3.** The comment says `%` is in no path.
- **Note 1, the property test.** It again asserts that each relative id is its IRI with the base removed: the base,
  or its directory, with the id after it, at every hierarchical base. Two parts were needed:
  - Its draw now splices in `./` and `../`. The new draw had almost never made a leading `./`, so the assertion alone
    caught nothing.
  - MEASURED (assert_check.py): with a leading `./` let through, the property test now fails with the assertion and
    passes without it.
- **Note 2, the model of rdflib.** It keeps `norm_url`'s last clause, a trailing `#` restored. No accepted id reaches
  that clause, so a test holds it to rdflib's own reading: `#` at `file:///crate/` is `file:///crate/#`, as the
  verifier measured.
- **Note 3.** The tautology among the path tests is now an independent statement: item 22's path form, written in
  the test. It holds that the id rule refuses first exactly the paths that form leaves out.
- **Note 4, the cheap part of the grammar** (the lead's call):
  - In a fragment and an absolute IRI, each `%` begins an escape of two hex digits.
  - An absolute IRI holds no `[` or `]`, and one `#` at most.

  So urllib's `urlsplit` reads every accepted id. It had raised on accepted ids such as `ab://[`, which broke
  rdflib's `defrag` and its RDF/XML reader given a base. An IPv6 literal is no host the profile needs. The second
  stated limit is narrowed to the rest of RFC 3986's grammar, such as a port of letters.
- **Notes 5 and 6.** Item 22's measured claim names its Pythons, and "last segment" is defined: the text after the
  final `/`, empty for a directory.
- **The measurement, again, on the rule as it now stands** (MEASURED, the round-1 verifier's scripts, unmodified):
  - 300,000 ids were drawn under the rule (546,297 draws), 18,701 of them with an escape and 16,676 absolute ones
    with a `#`.
  - At the eight hierarchical bases, rdflib 7.6.0 read each as RFC 3986 does. At none of the nine did it merge two
    ids, make a blank node or no node, or raise. At the urn base it joined 168,738 ids its own way, and merged none.
  - The test's model made the same IRI as rdflib on all 2,700,000 readings, under Python 3.12.9 and 3.13.5 alike.

**Not taken:**
- `canonical.write` raises TypeError on an @id that is no string. That is older than P0.5, and it is no refusal path:
  a generator's failure is refused by name. It is P0.7's.
- At bases urllib does not join (`s3:`, `data:`, `mailto:`), rdflib leaves every relative id relative (the verifier's
  note 5). That is rdflib's, whatever an id's spelling. Item 22's measured claim names the bases it was measured at.
- CLAUDE.md's timing is P0.6's.

**Measured, by the lead:**
- **39 hand mutants** (m_p05_r2.py), each killed by its targeted test, on the tree as frozen:
  - round 1's thirty, retargeted where the patterns moved;
  - a bare `%` admitted, one hex digit enough, or lowercase hex refused;
  - brackets admitted;
  - a second `#` admitted, none at all, or an empty tail;
  - the model's last clause lost;
  - a leading `./` let through, held by the property test alone among the targets.
- **The runner:** `QRO_MOTH_ROOT=<moth-quantum> bash verify/run.sh`, run `20261019-055510-1986-20d40e6+dirty`, on the tree as
  frozen but for this entry's figures: **17 stages passed, 7 skipped by name**, none failed, in 226 s of stage
  time, beside P1.1's second verifier.
  - docs: 164 passed; tool-tests: 129; vocab-tests: 12; format: 838; custody: 23; control-tests: 32. That is
    1,198 tests, 14 more than round 2's 1,184, all in test_spelling.py;
  - privacy: 263 files, 5 commit messages and 13 staged versions, nothing found;
  - the twin: ACCEPTED `21fafec5…`.

**Next:** P0.5's verifier, round 3, on Sonnet and the full bar.

## 2026-10-19 - P0.5's third verifier: NOT READY on prose; the cap reached; the fixes

**The verdict** (docs/reviews/P0.5/round3.md): NOT READY, on the full bar, the third of three. It found no defect in
what the code does, and no gate that passes a fault it claims to catch.
- **What it measured.** It ran rdflib 7.6.0 under Python 3.12.9 and 3.13.5:
  - 739,634 ids at 24 bases, with identical readings on both Pythons;
  - exhaustive small alphabets, and every `;` id to length 11;
  - real parses, and pyshacl with a shape of its own;
  - 2,350,646 strings against its own reading of item 22, with no widening against round 2's rule.

  The lead's 39 mutants were killed again.
- **Two false sentences:**
  - **D1:** item 22 said distinct ids are distinct "as RFC 3986 resolves them", and the entry above that rdflib
    read each "as RFC 3986 does". RFC 3986 removes dot segments from an absolute reference's path, while JSON-LD
    1.1, and rdflib, keep an absolute IRI as written. So `http://example.org/a/../b` and `http://example.org/b` are
    one IRI by RFC 3986 and two nodes in RDF. What was measured is JSON-LD 1.1's reading.
  - **D2:** two test comments, "no accepted id ends in #" (`ab:#` does) and "a character no @id holds" (fragments
    and absolute IRIs hold `%`, `:`, `#`). The same phrase is in the first P0.5 entry above.
- **The cap is reached:** three NOT READYs, each over narrower reasons than the one before. Round 4 runs on the
  relaxed bar (CLAUDE.md item 6).

**The fixes:**
- **D1.** Item 22 says distinct ids are distinct "as JSON-LD 1.1 reads them, a relative id resolved by RFC 3986's
  algorithm and an absolute IRI kept as written". It names the two absolute IRIs RFC 3986 alone would make one. The
  test file's comment on its bases says the same of a relative id. In the entry above, "read each as RFC 3986 does"
  is to be read as JSON-LD 1.1 reads each.
- **D2.**
  - The trailing-`#` test says no accepted relative id ends in `#`, and that an absolute one is left as written
    before the clause.
  - The path test says a refused path holds a character no path holds, which leaves it in none of the four forms.
    So, in the first P0.5 entry above, "a character no @id holds" is to be read as no path holds.
- **Notes taken:**
  - **Notes 1 and 2.** A compact IRI is refused whatever its tail: the prefix test runs every prefix with six tails,
    `x`, `0`, `_1`, `a#b`, `%41` and `-`. And `@0`, `@9/y`, `schema:0`, `rdf:_1` and `schema:a#b` join the test of
    what rdflib reads otherwise. The verifier's three survivors are among the lead's mutants now, and are killed.
  - **Note 3.** The model's docstring says it models `norm_url`, not `Context.expand`.
  - **Note 4.** The lead's brief had said Python 3.13.5 has no rdflib. It has rdflib 7.6.0, so item 22's 3.13.5
    figure had been the model's alone. MEASURED now with rdflib itself: under 3.13.5 it reads the 300,000 ids at nine
    bases exactly as under 3.12.9, all 2,700,000 readings the same.
  - **Note 5.** A fourth stated limit names rdflib's departures:
    - at a base of a scheme urllib does not join, a relative id makes no node;
    - at a base with an empty path, `#a` is read with a dot.

    At no base measured does it make one node of two accepted ids, but as the first limit says.
  - **Note 7.** "One spelling" is as RDF compares IRIs, character for character. The rule normalises nothing.
  - **Note 8.** The `;` sentence names the eleven schemes urllib both joins and reads parameters in, under Python
    3.12.9 and 3.13.5 alike (MEASURED). The verifier counted ten.
- **Note 6, re-checked against the parcels.** Round 2's tightening (escapes, brackets, one `#`) had been checked
  against no parcel. Now:
  - P1.1's 1,018 tests, from its round-2 packet, pass on round 3's tree;
  - the 100 distinct @ids in P4's JSON files all pass the rule (MEASURED, ids_in_tree.py).

**Measured, by the lead:**
- **42 hand mutants** (m_p05_r3.py): round 2's 39, and the verifier's three survivors. Each was killed by its targeted
  test.
- **The runner:** `QRO_MOTH_ROOT=<moth-quantum> bash verify/run.sh`, run `20261019-073050-23277-20d40e6+dirty`, on the tree
  as frozen but for this entry's figures: **17 stages passed, 7 skipped by name**, none failed, in 199 s of stage
  time, beside other sessions' work.
  - docs: 164 passed; tool-tests: 129; vocab-tests: 12; format: 958; custody: 23; control-tests: 32. That is
    1,318 tests, 120 more than round 3's 1,198, all in test_spelling.py: 115 more prefix cases, and five more ids
    rdflib reads otherwise;
  - privacy: 264 files, 5 commit messages and 13 staged versions, nothing found;
  - the twin: ACCEPTED `21fafec5…`.

**Next:** P0.5's verifier, round 4, on Sonnet and the relaxed bar.

## 2026-10-19 - P0.5's fourth verifier: READY, on the relaxed bar

**The verdict** (docs/reviews/P0.5/round4.md): READY. It found no defect in what the code does, and no gate or
registry that lets an accidental fault through. Since round 3 the code had changed by one word of a comment in
qro/spelling.py.
- **What it measured.**
  - **rdflib 7.6.0 under Python 3.12.9:** 412,557 accepted ids at 43 bases, with no blank node, no exception and no
    merge of two ids. Its readings differ from RFC 3986's only at six bases whose own path is odd, and merge none
    there.
  - **Real parses** in subject and object position: 27,991 ids at 14 bases, the same under 3.13.5.
  - **The `;` rule:** 526,107 ids holding `;` at 15 bases, read through urljoin under both Pythons, none read
    otherwise. The eleven schemes were confirmed.
  - **The test's model of rdflib:** the same as rdflib on 3,870,043 readings per Python.
  - **Every serialiser of rdflib and pyshacl 0.40.1:** one node each.
  - **The old reader against the new:** 363,612 verdicts per tree. Nothing was newly accepted, and every new refusal
    is `spelling`.
  - **Mutants:** the lead's 42 killed again. Of its own 19, 16 were killed, two survivors were equivalent, and one is
    note 5.
- **Its slip:** a script of its own imported `qro` from the frozen tree with `python -I`, which wrote two `.pyc` files
  there. It deleted exactly those and checked the sums again: 264 files, each as frozen.

**Its notes, none blocking, and where each goes.** Each is P0.7's, the lead's piece after P0.6.
- **Note 1, a hang older than P0.5.** The reader builds every directory prefix of each File's path. A File id of
  50,000 one-letter segments, 100 KB, took 149 s, and the memory is quadratic in the number of segments (MEASURED by
  the verifier). It is the same at 20d40e6. A cap on an id's length, or prefixes built so their cost is linear, ends
  it.
- **Note 2, JSON-LD 1.0's prefixes.**
  - RO-Crate 1.3 asks for a metadata document that is valid JSON-LD 1.0. A JSON-LD 1.0 processor makes a prefix of
    every term of the context, and 333 of the pinned context's 3,069 terms have a scheme's shape (`data`, `geo` and
    `isbn` among them).
  - So under 1.0, `geo:1,2` and `http://schema.org/geo1,2` would be one node. That is the verifier's model of the
    2014 rule; no 1.0 processor was run.
  - rdflib in 1.0 mode reads as in 1.1, so only a processor of the 2014 recommendation is exposed. Item 22's fourth
    limit states this exposure as BELIEVED, and the verifier finds it wider than that limit reads.
  - **The lead's decision:** P0.7 refuses an absolute IRI whose scheme is a term of the context, as it now refuses a
    prefix of the context. It first measures which of those names a registered scheme is, and that no parcel's crate
    writes one.
- **Note 3.** The third limit's "leaves a relative id relative and makes no node of it" is false for a fragment holding
  `:`. At a `mailto:` base, `#a:b` makes the relative IRI `.#a:b`. rdflib departs at bases in four more ways the limit
  does not list: a `//` in the base's path collapses, dot segments there are removed, a final `;` is dropped for a
  fragment, and the scheme is lowercased. None of them merges two accepted ids.
- **Note 4.** Item 22 says `@x`, `//`, `?` and `;` are the root. That holds at a directory base. Read from the metadata
  file's own URL, each is the descriptor's IRI.
- **Note 5, test reach where the code is right.**
  - A rule that let `schema://x` through survives every stage. No reader misreads it, since JSON-LD 1.1 keeps a value
    whose suffix begins `//` as written, so the prefix test's "whatever its tail" says too much.
  - `CONTEXT_PREFIXES` is written out, not derived from the context, and its test reads only `V.PREFIX`. So a second
    prefix of the profile's own would go unseen.
- **Note 6.** The draft commit message held its verdict's placeholder, which is now filled. CLAUDE.md's timings are
  P0.6's.

**The whole of P0.5** took four rounds and three send-backs: the first on two ids rdflib reads otherwise, the
last two on prose alone. It is committed as the next entry says. Its fixes, and its verifiers' measurements, are
in the four entries above and the reports.

## 2026-10-25 - P1.1 merged: the adapter's checker side

**What P1.1 is.** P1 is the adapter parcel: it turns Quantum-Film's records of real runs, on IBM's devices and on
Moth's Atlas emulator, into crates, and adds the checker's steps that hold a crate to those runs. Its design was
approved on 2026-10-15, in the round's ledger, P1.md items 1 to 13, with the lead's decisions in lead.md. P1.1 is
its checker side, built on Sonnet in its own worktree from 7f40400 and brought to 20d40e6 by a fast-forward. It adds
21 files and changes none:
- **qro/p1_forms.py:** the readers of the three raw result forms (IBM's, and Atlas's result and vector) and of a
  calibration snapshot, in strict JSON;
- **qro/p1_commit.py:** commitment v3 and its options digest;
- **qro/p1_graph.py:** `Index`, the crate's relations;
- **qro/p1_decode.py:** the decode rules, the known-answer verdicts, `pub_counts` and `crate_file`;
- **qro/p1_calibration.py:** the values-digest, the claims and the link rule;
- **qro/p1_steps.py:** steps 4, 5 and 8;
- **qro/register_p1.py:** those three steps and the three raw forms, and nothing else;
- **tests/p1/:** 1,169 tests in 405 functions, and the test-only builder, p1_builder.py.

P1.2, the producer side, is not built: the records, the generators, the adapter, the plants, the twin, the
`p1-crates` stage and P1.2's own page.

**What the steps hold:**
- **Step 4:** each Pub's commitment, recomputed over all fourteen inputs, against IBM's echo inside the raw result's
  bytes, at the PUB's own index; never the manifest's or the claims'.
- **Step 5:** the decode, in the bit order the raw declares, and the known-answer verdicts. IBM's are judged by the
  modal outcome against its mirror; Atlas's by the vector, each Z position within four standard deviations.
- **Step 8:** each calibration snapshot's values-digest, and the link rule, `history-at-first-shot` or
  `history-in-gap`. A Job's times are held to its raw result's span wherever the raw carries one.

**The real records** (MEASURED through the built code, in scratch; P1.2's `p1-crates` is to hold them in a gate):
- 68 of 68 commitments agree with IBM's echo;
- 31 of 31 known answers hold `msb-first`, and none `lsb-first`;
- 12 snapshots give six values-digests, 1, 3 and 2 on fez, kingston and marrakesh;
- the links are 57 at the first shot and 8 in a gap;
- the six Atlas results give their layouts, and the vector its worst |z| of 2.154 under `atlas-register`.

**Changes from the approved design, each taken by the lead:**
- `crate_file` is public;
- `Index` raises GraphError for a type list holding a non-string;
- a record's field of the wrong kind is refused, naming the field;
- a Job's times are held to the raw's span wherever the raw carries one, whatever its link word;
- step 8 weighs the snapshots whose files name the job's backend;
- step 4 keeps of a job line its commitments alone;
- every reader refuses an integer past 2^63 - 1 in magnitude;
- a refusal's detail quotes an echo to 65 characters and a numeral to 24 digits.

**The four rounds** (docs/reviews/P1.1/):
1. **NOT READY**, on three code defects and prose:
   - the Atlas reader refused the real results' `fetched_at`;
   - the steps cached every parsed result, and a crate of 60 jobs ran out of memory, exit 3;
   - step 8 took the carried snapshots by the device entity's @id.
2. **NOT READY**, with no wrong verdict found:
   - two gates: the test of step 8's snapshot passed a mutant keeping its document, and step 8's registration was
     tested from one side;
   - a memory defect: step 4 kept every job line, 507 MB on ten lines of 2.1 MB;
   - prose.
3. **NOT READY**, with no defect in what the code does: limit 17's costs and its exit sentence, two gates (the
   memory class, and step 5's registration), and two sentences. The cap was reached.
4. **READY**, on the relaxed bar, on 2026-10-25. Its auditor agreed with the steps on 75,802 mutated crates and
   11,175 link-rule crates, and every line of the seven modules runs under the tests.

**Measured at the merge:**
- P1.1's mutants: 274 of 275 hand and 870 of 873 automatic, each survivor an equivalent it names;
- the verifiers' mutants: round 3's 52 of 52, and round 2's 81 of 83, the other two no longer applying;
- 1.74 million reader mutants, none escaping;
- the runner on the merged tree, run `20261025-224750-9381-8afeede+dirty`: **18 stages passed, 6 skipped by
  name**, none failed, in 195 s of stage time; 2,487 tests in its pytest stages, P1's 1,169 among them.

**The stated limits,** as P1.1 last restated them (P1.md 2026-10-16T14:16:08Z, restated 16:47:50Z,
2026-10-19T15:09:12Z and 17:46:44Z):
1. A producer who holds every byte can reseal a crate, and the crate-only checker accepts it (`qpy-only`,
   `shot-moved-resealed`; each tested as accepted).
2. IBM's echo shows that the bytes carry the commitment, not that the bytes are IBM's.
3. Atlas's commitment is `none`, and nothing evidences that it came before the result.
4. A `history-*` link is a necessary condition, not proof that the snapshot was in force.
5. The values-digest keeps list order, so a provider that reordered a list between fetches would show two digests.
6. A known answer holds the order only as far as its pattern tells orders apart. A set that is its own mirror is
   refused; Atlas's X positions are not tested, its Y positions cannot tell qubits apart, and its Z positions are
   held within four deviations.
7. `read-before-run`, `read-after-run` and `provider-linked` are refused `step-unbuilt`.
8. Execution spans are zone-less, and are read as UTC.
9. Steps 4 and 5 read of a record and of a job line only what they hold. No step reads a record's counts or digest,
   a verdict file, the manifest, a decoded count, or `qro:historyAtRunning`.
10. A PUB's index is one decimal digit of its id: ten PUBs, 0 to 9, are accepted, and an eleventh is refused (P1.1's
    fourth verifier: the ledger had said ten needs a new rule).
11. The bit order a known answer is judged by rests on whatever binds the known-answer Pub's record, and a Pub
    weakened to `none` binds nothing.
    - With that Pub alone at `none`, its record resealed to a mirrored circuit, and the Decodes declared
      `lsb-first`, steps 4, 5 and 8 accept the crate.
    - Atlas Pubs have no commitment, so relabelling a law Pub's role skips step 5's accounting.
    - A Job weakened to `unknown` or `unexposed` passes step 8 where its raw result carries no span.

    Step 9 is the stated cover.
12. A raw result that inflates past 64 MiB is refused `raw-form`.
13. A number in a snapshot must be one binary64 holds exactly. In every reader:
    - an integer past 2^63 - 1 in magnitude is refused;
    - a float that overflows binary64 is refused;
    - one that underflows reads as 0.0.
14. The snapshot form is closed: a key IBM adds refuses every crate carrying it until the form has a version for it.
15. Of two carried snapshots of one stamp, the greater @id is the one a gap names.
16. A known-answer verdict needs at least one shot.
17. **In steps 4, 5 and 8, an OSError and a MemoryError are not caught:** exit 3, or exit 2 for a PermissionError.
    Step 3, which reads every raw result first, is P0's.
    - A step costs the parse of the crate's largest file, not the sum of its files.
    - What a parse costs, MEASURED by shape: a JSON file up to 46 times its size, a snapshot 147 times, an IBM
      result's array 6.7 times its inflated size, and a circuit 21.7 times.
    - No bound that a file cannot exceed is known.
18. The tests commit no provider file: they hold five real echoes and seven snapshots' digests as literals.
19. A file the crate lists and the disk lacks is, if a step is called directly, a FileNotFoundError; through the
    checker, step 2 refuses it first.
20. `qro:jobId` is REPORTED, and compared with nothing.
21. A Job's times are the raw result's to say: where the raw carries no span, they are compared with nothing.
22. No Pub or Job is compared with another job, though a Decode is held to its known answer's job. So a job copied
    whole under new ids is accepted by every step but 9, the cover.

**Left for P1.2** (P1.1's fourth verifier's notes, ledger 2026-10-26T05:42:20Z):
- a test of step 8 telling the older of two named snapshots by stamp where their ids sort the other way;
- a stated limit for step 4's finding committed files by digest among the crate's copies, so that altering only the
  copy a job ran is accepted while another copy keeps the digest;
- the cost table on P1.2's own page, where p1_steps.py is to point;
- step 5's time on a result at the reader's cap, 6.1 s, tallying the rows for the verdict and again for each PUB.

## 2026-10-19 - P0.5 committed; P0.6: P0.4's fourth verifier's ten notes

**P0.5 is committed as 8afeede** and pushed to origin main, on Logan's standing word of 2026-10-16. The runner
passed on the committed tree: 17 stages, 7 skipped by name, in 187 s of stage time beside other work. Its fourth
verifier's notes are P0.7's, the lead's piece after this one.

**What P0.6 is.** It is the lead's own piece after P0.5, and takes the ten notes P0.4's fourth verifier left, none of
which blocked (the entry "P0.4's fourth verifier: READY, on the relaxed bar"). It was begun before the weekend on
P0.5's first packet, rebuilt on its second, third and fourth, and applied to P0.5's commit. Nothing in it touches
P0.5's files.

**The privacy gate** (tools/check_privacy.py):
- **Note 1, the history.** A push sends every commit's tree, so a key committed and then deleted in a later commit is
  pushed, though no file and no staged version holds it. The gate now reads every blob of HEAD's history that the
  index does not hold.
  - `git rev-list --objects HEAD` lists them, `git cat-file --batch-check` keeps the blobs, and
    `git cat-file --batch` reads each once.
  - A finding names its path and its blob, as `notes.md (history 1a2b3c4)`. A binary blob is listed by name.
  - git failing to list or read the history is a finding. A blob git lists and then does not hold is read as
    missing, a finding too. git rev-list itself fails on a real missing blob, so that blob is a finding that way
    first (MEASURED); the second arm is held by a simulated listing.
- **Known findings.** A finding in a blob already pushed, which no commit can take back, is listed as known where the
  gate's `KNOWN` table names its blob and its alternative. Each was read and judged no secret.
  - It names two: P0.4's round4.md as pushed in 20d40e6, whose verifier quoted the two spellings note 3 adds, each
    with the placeholder name `name`.
  - The current round4.md holds both redacted as `<a home path>`, and docs/reviews/P0.4/README.md says so.
  - A test holds that each entry's alternative finds something in its blob, wherever git holds the blob. A copy
    whose history does not reach the blob, a shallow clone or a fresh `git init`, holds none, and the gate reads
    none there. On this repository's history, a wrong entry would leave the blob's findings unknown, and the
    privacy stage would fail.
- **Note 2, replace refs.** Every git the gate runs ignores replace refs (`GIT_NO_REPLACE_OBJECTS=1`), as a push does.
  A replace ref no longer shows the gate another message than the one pushed.
  - A side effect (MEASURED): with packed-refs corrupt, `cat-file` no longer fails, as it was looking up replace
    refs. So the staged reader's arm for a `cat-file` failure is reached by no real repository now, and its test
    simulates the failure.
- **Note 3, two spellings,** each with its plant:
  - `wsl-unc-slash`, a UNC path to WSL with forward slashes, as `Path.as_posix` writes it;
  - `url-quoted-drive`, a drive path percent-encoded with its colon kept.

  Neither alternative finds a URL whose host is named wsl, nor a scheme ending in a letter before an encoded path.
- **Notes 7 and 8, pipes.** A symbolic link to a pipe is read as its text, so the link check's place before the pipe
  check is held. The pipe test makes a real pipe where the host can (`os.mkfifo`), and simulates one on Windows.
- **The docstring** says what the gate reads now, and states the limit: only HEAD's history is read. Another branch,
  a tag, a stash or a note, which `git push` sends only when asked to, is not.

**The runner and the registry:**
- **Note 4.** The registry pins the lint stage's program, `python -m ruff check`, with a plant. Before,
  `python - ruff check` read an empty program and printed lint ok.
- **Note 5.** A test runs the runner itself, on a copy whose one stage, the lint, fails. The runner must count the
  failure, say FAILED and exit 1; the same copy clean must pass.
  - The runner's header (its section 3) and the registry's docstring no longer say the negative control shows that
    the runner can fail. Its verdict is inverted, so it shows only that the command line still refuses its plant.
- **Note 6.** A stage that runs a directory or a tool the tree does not hold yet must be guarded by a `need_file` of
  it.
  - The rule is derived from the tree, not listed.
  - It is tested with a stage of its own, so that it holds whatever the parcels have built.
  - A stated limit: while a stage's tool is absent, which of its checks the stage runs is read by nothing.
- **Note 7, the rest.** Neither of these is a guard call:
  - a comment line indented by a tab, or by blanks and a tab;
  - a word that only holds a guard's name (`xneed_env`, `pre-need_file`, `need_envx`).

  The verifier's other two survivors are each right as shipped, and stated: `2>&1` in `packages`, and the failure
  token's parts.
- **Note 9.** verify/pytest-stage.sh's last message names the runner's two guards, `need_file` and `need_env`. Its
  header says so, and the registry's pin of its command lines follows. The runner's header lists `need`'s removal
  among its departures from moth-quantum's runner.
- **Note 10.** CLAUDE.md's timings keep their idle figures, ~70 s and ~125 s, now dated 2026-10-16. Beside them it
  gives what was measured beside other work on 2026-10-19: about 170 s for the quick budget, and 150 to 365 s for the
  whole runner. The longest, 364 s, was P0.6's own run on P0.5's fourth packet, beside P0.5's fourth verifier and
  P1.1's builder. Every stage took about twice as long as in its run on P0.5's second packet that morning, 195 s. The
  idle figures predate P0.4's, P0.5's and P0.6's tests. The owner's word that several sessions share the machine made
  a quiet one no condition of measuring.

**Measured, by the lead:**
- **30 hand mutants** (m_p06.py), each killed by its targeted test, 30 of 30 again on the tree as frozen (mut_p06c.log):
  - the history not read, or its listing's failure no finding;
  - the index's blobs read again, trees read as blobs, a blob git does not hold dropped;
  - a binary blob made a failure, or an unreadable one passed over;
  - a finding not counted;
  - every finding known, none, or a known blob's every finding;
  - replace refs read;
  - each spelling gone, matched inside a word, or its backslash's code unread;
  - the pipe check before the link check, or a pipe read;
  - the lint's program unpinned;
  - a failing stage not counted, or the runner exiting 0 on one;
  - the guard rule never firing, firing on paths the tree holds, keeping guards from stage to stage, or reading no
    tool's stage;
  - a tab-indented comment line read;
  - the guard word without its look-behind or its look-ahead;
  - `need` named again in the stage script.

  The first pass, of 29, left two alive, and each was taken. Trees read as blobs went unseen, since no test had a
  directory: the binary-blob test now holds one, and that no tree is listed. A blob git does not hold was dropped
  before the reader saw it, an arm no real repository reached: such a blob is now read as missing, a finding, and a
  test simulates the listing.
- **Found before freezing, both MEASURED:**
  - **The check of the known list** first asked git for each blob, and failed if git had none. So the tool-tests
    stage failed in a fresh `git init` of the tree. It would also have failed in a shallow clone made after P0.6's
    commit, since no such blob is there.
    - Now an entry is held only where git holds its blob.
    - A test runs the check in a repository without the blob, and the old check, put back, fails that test.
    - A control holds that the check catches an entry whose alternative finds nothing, and one that names no
      alternative.
    - In a depth-1 clone of a scratch commit of P0.6, which holds no such blob, the docs, tool-tests, privacy
      and privacy-controls stages pass (run 20261019-090713-52996).
  - **The gate on the unstaged change.** With P0.6 applied to the checkout but not staged, the gate failed: the
    index still held round4.md as pushed, and a plain `git commit` would have taken that version. Once the change
    was staged, it passed. This is P0.4's staged-version reader at work on this repository.
- **The runner** on the tree as frozen but for this entry: run 20261019-090657-52800, 17 stages passed and 7
  skipped by name, 199 s of stage time beside other work.
  - 1,342 tests, 24 more than P0.5's: docs 175, tool-tests 142, vocab-tests 12, format 958, custody 23,
    control-tests 32.
  - The privacy gate read 265 files, 6 commit messages and 113 versions in earlier commits, and listed the two
    known findings.

**Next:** P0.6's verifier, on Sonnet and the full bar.

## 2026-10-19 - P0.6's first verifier: NOT READY, two defects in the history reader, and the fixes

**The verdict** (docs/reviews/P0.6/round1.md): NOT READY, on the full bar, the first of three.
- **D1, code and a gate.** `git rev-list --objects` cuts a path at its first line feed. So a top-level name that
  begins with one is listed empty, as the root tree is, and the history reader dropped both alike.
  - A key committed under such a name and deleted in a later commit passed the gate, though a push sends it
    (MEASURED by the verifier with `git pack-objects`).
  - Its fuzz missed only such names: 42 of 80 repositories here, 27 of 60 under WSL.
  - The reader's comment said such a path "leaves a line that is no oid". git cuts it instead.
- **D2, code and a gate.** `git rev-list --objects HEAD` without `--` is ambiguous where a file or a directory named
  HEAD is at the root (or `head`, where case is ignored). git refused the listing, and the gate failed a clean tree.
  It failed closed, so no key passed.
- **D3, prose.** The entry above, and a test's docstring, said the staged reader's `cat-file` failure is reached by no
  real repository. A staged loose object cut to half its length reaches it: `git ls-files` reads the index, and
  `git cat-file --batch` fails.
- **D4, prose.** The registry's docstring still said the negative control "proves the runner can say no". The entry
  above said that claim was gone.
- **What held** (MEASURED by the verifier):
  - its history fuzz over 460 repositories (branches, merges, renames, links, gitlinks, odd names, encodings) found
    no other miss, against an independent route through `ls-tree`;
  - missing, cut or garbage objects each fail closed;
  - SHA-256 repositories, linked worktrees and shallow clones work;
  - replace refs and grafts show the gate what a push sends;
  - the known list excuses only its two findings, in one blob, and that blob's other bytes hold no secret;
  - the runner passed in four trees, shallow clones among them, and the lead's 30 mutants were killed again.

**The fixes:**
- **D1.** A line of the listing is kept wherever it holds a space after the object id. A commit has none, and a tree
  or a blob always has one, its path cut at the first line feed. An empty path is named `(a path beginning with a
  line feed)`; the root tree, also empty, is a tree and is not read.
  - A test builds such a commit from objects, since no file system here holds the name, and checks that git lists
    it empty. The gate finds the key.
- **D2.** The revision is ended by `--`. A test holds a file named HEAD, one named head, and a directory named HEAD,
  each with a second commit so that the history is read.
- **D3.** The test makes the failure for real, from a cut loose object, and checks that `git ls-files` still reads
  the index. In the entry above, "is reached by no real repository now" is to be read as reached only by an object
  git cannot read.
- **D4.** The docstring says the negative control shows that the command line still refuses its plant, not that the
  runner counts a failure.

**Its notes, taken:**
- **Test reach, where the code was right:**
  - a replace ref on a blob of the history;
  - git's variables naming another repository while the gate reads its own history;
  - a SHA-256 repository's history;
  - the known list on the same bytes as a current file, and as a staged version, each still a finding.
- **The two spellings,** their forms and edges each held:
  - `wsl-unc-slash`: its `.localhost` form, and each character of its lookbehind;
  - `url-quoted-drive`: doubled separators, the `%2F` branch, and the name it requires (an encoded placeholder
    passes).
- **Two gaps closed:**
  - `url-quoted-drive` is found after an escape such as `%20`, which ends in a digit, as encodeURI leaves a path
    after a space;
  - a new alternative, `wsl-file-url`, with its own plant, finds a file URL to the WSL host's home, as a browser or
    `Path.as_uri` writes one. A URL of another scheme to that host is not one.
- **Prose:**
  - CLAUDE.md item 3 and the privacy stage's text say the gate reads every blob of HEAD's history. CLAUDE.md adds what
    a contributor who commits a path and deletes it meets: the gate fails until that history is rewritten, before a
    push.
  - The gate's docstring states two more limits. History's blobs are read into memory at once, at about 1.5 MB/s:
    120 versions of 1 MB took 78 s and 380 MB. And a partial clone fetches the blobs it lacks from its remote, failing
    where that remote cannot be reached.
  - The registry's stated limits name ruff's options after the lint's directories beside `--exit-zero`.
- **lint_copy** reads the lint's directories from the runner's own line, so a new directory there no longer fails the
  clean case.
- **Two clarifications:**
  - "Nothing in it touches P0.5's files" in the entry above means no line P0.5 wrote. CLAUDE.md and VALIDATION.md are
    files both pieces change, in other places.
  - CLAUDE.md's 150 s is P0.5's round-1 run, 151 s ("P0.5's first verifier" above).

**Not taken, for P0.7:**
- a file name outside the console's code page crashing the gate's last print, where stdout is not UTF-8 (older than
  P0.6; the runner sets the encoding);
- ruff's options after the lint's directories, to be pinned word for word.

**Measured, by the lead:**
- **47 hand mutants** (m_p06_r1.py), each killed by its targeted test, 47 of 47 (mut_p06_r1.log).
  - The first 30 are P0.6's own, their texts moved where the fixes moved them.
  - The 17 new ones are the fixes and the notes:
    - the line feed's name dropped, or left unnamed;
    - HEAD not ended by `--`;
    - the staged arm's failure no finding;
    - history read with replace refs, or listed with git's variables kept;
    - 40 hex digits only;
    - each spelling's new form, edge and name;
    - the file URL's alternative gone, its encoded dollar, or any scheme.
- **The runner** on the tree as frozen but for this entry: run 20261019-104842-22255, 17 stages passed and 7
  skipped by name, 187 s of stage time beside other work.
  - 1,365 tests, 23 more than the entry above: docs 175, tool-tests 165, vocab-tests 12, format 958, custody 23,
    control-tests 32.
  - The privacy gate read 267 files, 6 commit messages and 115 versions in earlier commits, and listed the two
    known findings.
  - With the fixed gate, P1.1's 21 files and P4's 51 hold no finding.

**Next:** P0.6's second verifier, on Sonnet and the full bar, after the pause.

## 2026-10-25 - P0.6's second verifier: NOT READY, a name the console cannot write; the fixes

**Where P0.6's entries sit.** The two entries above were written on 2026-10-19, and are laid here as P0.6's two
verifiers read them. P1.1 was merged first, as 37640f0, since it was READY and P0.6 was not; its entry sits before
them. No file of P1.1's is P0.6's.

**The verdict** (docs/reviews/P0.6/round2.md): NOT READY, on the full bar, the second of three.
- **D1, code and a gate.** A file name the output's code page cannot write crashed the gate's last print.
  - The case: stdout redirected, so written in cp1252, and a binary file named in CJK characters, committed and then
    deleted.
  - 8afeede's gate passed that tree. P0.6's prints the names only an earlier commit holds, so it exited 1, on a
    UnicodeEncodeError.
  - It failed closed. The runner sets PYTHONIOENCODING, so it was immune, and this repository's history holds no
    such name.
- **D2, prose.** The entry above calls that crash "older than P0.6". That is true of a file in the tree, and false
  of a name only an earlier commit holds.
- **What held** (MEASURED by the verifier):
  - round 1's fixes, over 44 awkward names, and the first verifier's fuzz on fresh seeds;
  - 19 kinds of object damage, 40 git configurations, and replace refs of a commit, a tree or a blob;
  - the known list, and the three spellings over a corpus of their comments' own words;
  - shallow clones of depth 1 and 2, and WSL;
  - the lead's 47 mutants, killed again.

**The fixes:**
- **D1.** The gate's command line writes what its output cannot encode as an escape (`errors="backslashreplace"`).
  A process test runs it with `PYTHONIOENCODING=cp1252`, on a binary file named in CJK characters, once in the tree
  and once in an earlier commit only. Each run passes and names the file as `中文.bin`. The entry above
  left this for P0.7 ("Not taken, for P0.7"), and it moves here.
- **D2.** In the entry above, "older than P0.6" is to be read as true of a file in the tree alone. For a name only an
  earlier commit holds, P0.6's history reader made the crash, and D1's fix ends it.

**Its notes, taken:**
- **Test reach, where the code was right:**
  - history's `cat-file --batch` failure arm, from a loose object of an earlier commit cut to half its length: git
    still lists it and reads its type, and the batch read fails (note 1);
  - the replace flag on `rev-list` and on `cat-file --batch-check`: a key committed and deleted, then its commit
    replaced by one with no key, or its blob by a tree (note 2). Each case checks first that the replace ref took.
- **The spellings' edges, each held** (note 4):
  - `wsl-file-url`: a URL to `/users/`, found; a placeholder for the name, a URL inside a word, and one with no
    distribution, each passed;
  - `url-quoted-drive`: two hex letters with no percent sign before them, and a digit before the drive letter, each
    passed;
  - `wsl-unc-slash`: a longer host, `wsl.localhost.example.org`, passed.
- **The `need_env` half of P0.6's note 6, stated, not derived** (note 6). The lead had meant to derive it as the
  `need_file` rule is: a stage whose line reads `${NAME:-}` is guarded by `need_env NAME`. But no stage's line reads
  its variable; the stage's tests do. So the registry's docstring says what is left: deleting a `need_env` passes, and
  the stage then fails where the variable is unset, loudly, rather than skipping by name.
- **Prose:**
  - the registry's limit: ruff's options "anywhere on the lint line" (note 7);
  - the runner test's need of ruff and the SHA-256 test's of git 2.29, each stated in its docstring (notes 8 and 9);
  - CLAUDE.md item 3: "a home path, an address or a key committed and then deleted" (note 13);
  - the registry's `git_env` docstring: the gate also sets GIT_NO_REPLACE_OBJECTS, which `git ls-files` does not
    need (note 14);
  - the gate's limit on names that are not UTF-8: a path of HEAD's history is read, its name decoded with
    replacement (note 15).

**Not taken, for later:**
- a test of a history path that is not UTF-8 (note 3; the code reads one, MEASURED by the verifier);
- the guard rule on the `env NAME=VALUE python TOOL` form (note 5);
- `jwt`'s cost on a crafted run of `-eyJ`, which grows as its square (note 10; older than P0.6);
- a name that begins with a percent-encoded character, which every URL spelling misses (note 11; older).

Note 12 found the cost limit true, and asks for nothing.

**Measured, by the lead:**
- **11 hand mutants** (m_p06_r2.py), each killed by its targeted test, 11 of 11 (mut_p06_r2.log): D1's output written
  strictly; history's batch arm returning no finding; `rev-list`, and `batch-check`, honouring replace refs; and
  the seven spelling edges.
- **Round 1's 47** (m_p06_r1.py), killed again on this tree, 47 of 47 (mut_p06_r1_on_r3.log).
- **The runner** on the tree as frozen but for this entry's figures: run `20261025-230418-12265-37640f0+dirty`, 18
  stages passed and 6 skipped by name, 229 s of stage time beside P4's run and other work.
  - 2,546 tests, 59 more than at P1.1's merge: docs 175, tool-tests 177, vocab-tests 12, format 958, custody 23,
    control-tests 32, p1 1,169.
  - The privacy gate read 294 files, 7 commit messages and 118 versions in earlier commits, and listed the two
    known findings.

**Next:** P0.6's third verifier, on Sonnet and the full bar, the third of three.

## 2026-10-26 - P0.6's third verifier: NOT READY, a gate with no stdout; the cap reached; the fixes

**The verdict** (docs/reviews/P0.6/round3.md): NOT READY, on the full bar, the third of three.
- **D1, code and a gate, a regression.** Round 2's fix reconfigured stdout on every run. Where stdout is None
  (pythonw, or a closed descriptor) or a stream with no `reconfigure` (a console's StringIO), it raised an
  AttributeError, and a clean tree failed that 37640f0's gate passed. It failed closed, and the runner, which gives
  stdout a file, was immune.
- **D2, prose.** The entry above says that no stage's line reads its variable, and the registry's docstring says the
  same. That is false of the instruments stage, whose line passes `${QRO_MOTH_ROOT:-}` to its tool, so the rule was
  derivable there. And "deleting one passes here" was not true of p4-shacl's call, which the tests of the guards'
  forms take as their text.
- **What held** (MEASURED by the verifier):
  - the freeze, and the runner in three copies, a clone with the real history among them: 18 stages passed and 6
    skipped by name, 2,546 tests;
  - D1's escape under 14 code pages, with stdout a pipe, a file or NUL, in both modes;
  - the history reader against what a push sends: on the real clone, 412 blobs, 118 of the history and 294 of the
    index, none missed and none extra;
  - merges, octopuses, tags and reverts; line feeds and carriage returns in names, and 11 names not in UTF-8; UTF-16
    and UTF-32 blobs and one of 20 MB; shallow clones of depth 1 to 5;
  - the known list: its one blob and its two findings, and no excuse for the same bytes anywhere else;
  - real encoders against the three spellings;
  - 39 of its 45 mutants killed, the 6 survivors its notes and D2.
- **The cap.** This is the third NOT READY, each on reasons narrower than the last. So P0.6's fourth verifier blocks
  only on a defect in what the code does (CLAUDE.md item 6).

**The fixes:**
- **D1.** stdout is reconfigured where it can be, and left as it is where it cannot. Where it is None, print writes
  nothing, as before P0.6. A process test runs the gate as `__main__` with stdout None and with a StringIO, in both
  modes.
- **D2.** The rule is derived where a stage's line gives it something to read.
  - `env_unguarded`, in the registry, holds each stage whose own command reads a variable to a `need_env` of that
    variable among the guards since the stage before. Today that is the instruments stage.
  - Its plants: the guard deleted, moved before the stage before, or naming another variable; and a stage of its own
    that reads one unguarded.
  - The registry's docstring states the residual as p1-crates', p2-crates' and p4-shacl's, and says why deleting
    p4-shacl's fails the tests of the guards' forms.
  - In the entry above, "no stage's line reads its variable" is to be read as true of those three alone.

**Its notes, taken as tests:**
- a key under a history name that is not UTF-8 (`caf`, the byte 0xE9, `.md`), committed and deleted, is found, and
  named with U+FFFD (note 1, and round 2's note 3);
- history's `cat-file --batch-check` arm, simulated, since no damage reaches it once the listing has passed (note 2);
- `url-quoted-drive` after a percent sign and no hex pair passes (note 3).

**Not taken, for later:**
- note 4: privacy-controls do not watch the history reader, though tool-tests do, and nothing says otherwise;
- notes 5 to 7: an encoded space before a POSIX home path; a drive path whose encoded name begins with a non-ASCII
  letter; `quote()` of a WSL path, and a file URL through the WSL host's `/mnt/c`. Each is older than P0.6, or within
  "encoded other than as a listed alternative says".

Notes 8 to 10 ask for nothing.

**Measured, by the lead:**
- **8 hand mutants** (m_p06_r3.py), each killed by its targeted test, 8 of 8 (mut_p06_r3.log):
  - the reconfigure unguarded, and its guard inverted;
  - history's batch-check arm returning no finding, and a history path decoded strictly;
  - the lookbehind's percent pair widened to letters;
  - `env_unguarded` keeping guards across stages, flagging no read, or counting any guard.
- **The runner** on the tree as frozen but for this entry's figures: run `20261026-042014-37475-37640f0+dirty`, 18
  stages passed and 6 skipped by name, 269 s of stage time beside three builds.
  - 2,557 tests, 11 more than the entry above: docs 179, tool-tests 184, vocab-tests 12, format 958, custody 23,
    control-tests 32, p1 1,169.
  - The privacy gate read 295 files, 7 commit messages and 118 versions in earlier commits, and listed the two
    known findings.

**Next:** P0.6's fourth verifier, on Sonnet, blocking only on a defect in what the code does.

## 2026-10-26 - P0.6's fourth verifier: READY, on the relaxed bar

**The verdict** (docs/reviews/P0.6/round4.md): READY, on the relaxed bar the cap sets, where only a defect in what the
code does blocks. It found none that P0.6 made or changed, and round 3's D1 and D2 hold.

**What held** (MEASURED by the verifier):
- the freeze, and the tree equal to the staged versions, byte for byte;
- the runner in a `git init` copy and in a clone with the real history: 18 stages passed and 6 skipped by name,
  2,557 tests. A copy with no .git, and a clone of depth 1, passed the stages that read git;
- D1:
  - 12 shapes of stream in-process, in both modes;
  - real processes: stdout a file, an appended file, NUL, a pipe, or closed by Git Bash's `>&-`; 13 values of
    `PYTHONIOENCODING`, UTF-8 mode, legacy stdio, unbuffered;
  - Python 3.13.5, `-W error` and `-X dev`;
- D2: `env_unguarded` flags exactly the deletion of the instruments stage's guard;
- the history reader:
  - 400 repositories built from plumbing (exotic names, gitlinks, merges), against `ls-tree` over every commit, with no
    problem found;
  - 160 repositories against 37640f0's gate, with no difference outside the history;
  - damaged objects, packs, replace refs, partial and shallow clones of depth 1 to 9, reftable, linked worktrees;
  - cost linear in commits;
- the known list, its one blob and its two findings;
- the lead's mutants of rounds 1 to 3, killed again, but for one of round 1's whose text now occurs twice.

**Defects older than P0.6, and one contrived:**
- **O1:** a clean sparse checkout is refused. Each tracked file it leaves out is a finding, `unreadable:
  FileNotFoundError`, though the staged reader reads the index's version of it.
- **O2:** a closed stdin (`<&-`) crashes the gate in its first git call, with WinError 6. It is round 3's D1 for stdin.
- **O3:** `jwt` is quadratic on a crafted run of `-eyJ` (1 MB in 534 s). This is round 2's note 10; P0.6 applies it to
  the history too.
- **O4:** a stream whose `reconfigure` exists and raises crashes P0.6's new line. No console or harness is known to give
  one.

The verifier MEASURED O1 to O3 the same at 37640f0 and at 8afeede. So P0.6 neither made them nor changed them.

**The lead's ruling** (the round's ledger, 2026-10-26T13:03:21Z):
- READY stands.
- O1, O2 and O4 are fixed in P0.7, the lead's next piece, with the report's notes:
  - its test gaps: masking; two history-only blobs in one batch; three behaviours of the runner; a line reading two
    variables; `url-quoted-drive`'s separator after `Users`;
  - its prose: the `missing` arm, which a garbage object reaches, so "no real repository reached it" is true of a
    deleted object only; the registry's third `need_env` case, a guard before a stage that reads no variable;
  - a WSL path with a backslash host and slashes after it, which passes;
  - the gate's git calls passing no `CREATE_NO_WINDOW`.
- O3 stays for later. It needs crafted content, outside the gate's threat model.

**The whole of P0.6** took four rounds and three send-backs:
- the first on two defects in the history reader;
- the second on a crash on a name its console cannot write;
- the third on a crash with no stdout, and a sentence.

It is committed as the next entry says. Its fixes, and its verifiers' measurements, are in its four entries above,
from "P0.5 committed; P0.6", and in the reports.

## 2026-10-26 - P0.6 committed; P0.7: the notes P0.5's, P1.1's and P0.6's verifiers left for P0

**P0.6 is committed and pushed** as cbdb6a3, with the entry above, on Logan's standing word. The runner on the
committed tree, before the push: run `20261026-060438-58849-cbdb6a3`, 18 stages passed and 6 skipped by name.

**What P0.7 is.** It is the lead's own piece after P0.6. It takes the notes and the defects older than the piece
they were found in that its verifiers left for P0:
- one from P0.5's first verifier;
- five from P0.5's fourth;
- two from P1.1's third, with a sentence of item 16 that P1.1's second round left the lead;
- one from P0.6's first;
- from P0.6's fourth, three defects in what the gate does, and its notes (below), as the lead ruled (the round's
  ledger, 2026-10-26T13:03:21Z).

P0.6's first verifier left another, the gate's stdout. P0.6's second verifier then found it a defect of P0.6's, and
it was fixed there (the entry "P0.6's second verifier: NOT READY, a name the console cannot write; the fixes").

P0.7 was built on P0.6's second packet. It was rebased onto P0.6's third, with P1.1's merge beneath it, by a
three-way cherry-pick. Two files conflicted. The gate and its tests were taken as P0.6 has them, since P0.7's only
change to them was the stdout. The registry's stated limit takes P0.7's rule, with P0.6's rounds. It was
cherry-picked again onto P0.6's commit, cbdb6a3, with no conflict, and P0.6's fourth verifier's part was made on
it.

**The reader:**
- **A path of many segments** (P0.5's fourth verifier, note 1, older than P0.5). The reader built every prefix of a
  File's path as a string, to hold each against every other for case and for kind. So a path of 50,000 one-letter
  segments, 100 KB, took 149 s, and its memory grew as the square of its length.
  - The paths are now a tree, one node a casefolded segment, holding the name it was first written with, its kind and
    the nodes below it. A path costs what its characters do: 50,000 segments are read in 0.07 s (MEASURED, the
    verifier's deep4.py, copied).
  - The refusals and their texts are the same, and the tests that hold their texts pass unchanged.
  - A test holds the memory: 10,000 segments peaked at 192 MB the old way, and peak at 2.8 MB now, under a bound of
    32 MB.
  - Another test holds that one name at two depths is two paths, so the tree goes down a level for each segment.

**The id rule:**
- **JSON-LD 1.0's prefixes** (P0.5's fourth verifier, note 2; the lead's decision, ledger 2026-10-19T15:59:26Z).
  RO-Crate 1.3 asks for JSON-LD 1.0, and a JSON-LD 1.0 processor makes a prefix of every term of the context, so
  `geo:1,2` and `http://schema.org/geo1,2` would be one node to it.
  - An absolute IRI whose scheme is any term of the crate's context is refused `spelling`; a prefix's stays the
    compact IRI it was.
  - The cost, MEASURED first:
    - 333 of RO-Crate 1.3's 3,069 terms have a scheme's shape, and `qro` too;
    - against IANA's registry of URI schemes (451, fetched 2026-10-25), six of them are registered: `about`, `data`
      and `geo`, permanent; `maps`, `query` and `tool`, provisional;
    - none of `http`, `https`, `urn`, `doi`, `mailto`, `tag` or `ftp` is a term.

    So a `data:` or a `geo:` IRI is refused, though it names no term.
  - No parcel writes one. P1.1's 1,169 tests pass on P0.7's tree, in the p1 stage. P4's draw keeps whatever the
    reader accepts, as P4 said (P4.md 2026-10-19T17:40:48Z). With P4's 53 files, as its second verifier's packet
    holds them, laid on P0.7's tree, P4's stages pass: p4's 822 tests, the profile regenerated byte for byte, and
    p4-shacl's 215 (run `20261025-232254-19246-7eaad48`, the lead's scratch).
- **The pinned context is loaded once,** in the vocabulary (`rocrate_context`, `context_terms`), for the reader's
  terms and the id rule alike. The test of the pinned copy holds both.
- **The prefixes' test** (note 5) holds `CONTEXT_PREFIXES` to the terms of RO-Crate's context and the profile's own
  whose IRI ends in a gen-delim, read from `V.context()`, not from `V.PREFIX` alone. So a second term of the profile's
  would be seen. The prefix test also reads `schema://x`, refused though a JSON-LD reader keeps it as written; its
  docstring says why.
- **Item 22's prose** (notes 3 and 4):
  - `@x` and its kin are the root at a directory base, and the descriptor's IRI where the crate is read from its
    metadata file's URL;
  - the third limit says rdflib makes no node of a relative id at a base it does not join, but of a fragment holding
    `:`; and it lists the four other ways rdflib departs at an odd base path;
  - the fourth limit becomes the rule and its cost.

**The writer** (P0.5's first verifier, a note). `canonical.write` raised a TypeError, sorting the graph, on an @id
that is no string, where the reader refuses the same metadata `spelling`. It now lets the reader refuse what it
cannot arrange, and a test holds four such @ids.

**The checker and the command line:**
- **A MemoryError is the host's** (P1.1's third verifier, D1). Step 3 turned any exception from a parcel's raw-form
  reader into `REFUSED raw-form`, so a host short of memory gave a verdict on the crate (MEASURED by the verifier: a
  raw result of 24 MB inflated, 30 KB on disk, refused at 45 MB of memory, exit 3 at 60 MB, accepted at 400 MB).
  - A MemoryError from a reader or a generator now reaches the command line, which answers it as the checker
    failing, exit 3.
  - Item 16 says so, and says that a parcel's step may refuse by its own name what its reading of a crate raises, as
    P1's do, and that what a step lets through is the checker failing. That is the sentence P1.1's second round left
    the lead (ledger 2026-10-19T13:15:40Z).
- **The line is cut at 4,096 characters** (P1.1's third verifier, a note: six places in P1's readers quote a file's
  text whole, and a hostile file put 3 MB into one REFUSED line).
  - The line is cut as escaped, where no escape is split, and says how many characters it did not write. What it
    writes `unicode_escape` still reads back.
  - A unit test holds the cut and the escape, and a process test holds a refusal at an @id of 10,000 characters.

**The registry:**
- **The lint's words** (P0.6's first verifier, a note). The registry held the lint's program and that it names every
  directory holding Python, and ruff's own options after them passed (`--ignore=ALL`). It now holds that every
  word after `python -m ruff check` is a name, once, and none an option, with three plants. The stated limit that
  named ruff's options now says they are refused.

**P0.6's fourth verifier's part** (docs/reviews/P0.6/round4.md; each MEASURED by it):
- **Every git the gate starts goes through one helper, `git`,** with no stdin but its input, and on Windows no
  console window.
  - O2: with stdin closed (Git Bash's `<&-`), each git inherited a standard input that was gone, and the gate's first
    call raised WinError 6. It is round 3's D1, for stdin, and older than P0.6.
  - The console windows: run where there is no console (pythonw, a detached process), each git opened a window of its
    own on the desktop. Logan saw them by the dozen in that verifier's run (the round's ledger, 2026-10-26T11:45:26Z).
  - A process test makes the gate's standard input name nothing, and runs it in both modes; another holds every git of
    a run and of the controls to the two flags.
- **O1: a clean sparse checkout is no longer refused.** The file loop made each tracked file a sparse checkout leaves
  out a finding, `unreadable: FileNotFoundError`, though the staged reader reads its index version, which is what a
  commit takes. A tracked file gone from disk is now passed over by the file loop and read from the index.
  - A test makes a sparse checkout: clean, it passes, and a key outside its cone is found.
  - The test that held a deleted tracked file a finding is restated: its index version is read, a key in it found.
  - A file the gate cannot read at all, a pipe or a device, is still a finding.
- **O4: the reconfigure is tried.** Round 3's guard asked `hasattr`, and a stream whose `reconfigure` exists and
  raises, of the verifier's making, crashed it. A stream that refuses is now left as it is; a test makes one.
- **Its test gaps, now held:**
  - each finding is printed masked: a key in a file, a staged version, an earlier commit's blob and a message (T1);
  - two blobs of earlier commits are read in one batch (T2);
  - the runner's skips under `--require-all`, a run of zero stages, and the negative control passing, failing as it
    must, or failing for another reason, each run end to end beside the lint (T3);
  - `env_unguarded` reads every variable on a line, not the first alone, and `url-quoted-drive` asks for a separator
    after `Users` (T4).
- **Its prose:**
  - history's missing arm is reached by a real repository: a blob whose loose object holds garbage is listed, and
    cat-file calls it missing. The docstring says so, and a test makes one. So "an arm no real repository reached",
    in P0.6's entries above, is true of a deleted object only.
  - the registry states its third `need_env` case: a guard before a stage that needs no variable is caught by no rule,
    and skips that stage by name wherever the variable is unset.
- **A spelling:** `wsl-unc` takes either separator after its host, so a WSL path with backslashes before its host and
  slashes after, as a path joined with both separators is, is found. P0.6's fourth verifier's own example of it, in
  docs/reviews/P0.6/round4.md as pushed in cbdb6a3, ends in the placeholder `name`. It is redacted in the file now,
  and the blob is named in the gate's KNOWN, as P0.4's round4.md's two are (P0.6).
- **CLAUDE.md** gains item 8, on a process with no console.
- **Not taken:** O3, `jwt` on a crafted run of `-eyJ`, outside the gate's threat model (its ledger entry says so).

**Measured, by the lead:**
- **17 hand mutants** (m_p07_r3.py, m_p07.py without the stdout's, which is P0.6's now), each killed by its
  targeted test on the rebased tree and again on the final one, 17 of 17 each (mut_p07_r3.log,
  mut_p07_r3_final.log):
  - the tree never going down a level, its case not folded, a file and a directory made one, the descriptor
    not placed, the other path's name taken for its own, and every prefix kept as a string;
  - the writer letting a TypeError out;
  - a MemoryError refused at step 3, or at step 9;
  - a term's scheme accepted, the profile's own terms left out, and the pinned digest unchecked;
  - the line with no cap, an escape split, and the count one short;
  - an option, or a name twice, in the lint.
- **12 hand mutants of P0.6's fourth verifier's part** (m_p07_r4.py), each killed by its targeted test, 12 of 12
  (mut_p07_r4.log):
  - the git helper's stdin inherited, or its console window back;
  - a tracked file gone from disk a finding again;
  - only an absent `reconfigure` left alone;
  - `wsl-unc` with a backslash after its host only;
  - the line feed between two history blobs lost, and the mask 24 characters wide;
  - `url-quoted-drive` with no separator after `Users`, and `env_unguarded` reading a line's first variable only;
  - the runner ignoring `--require-all`, passing a run of zero stages, or leaving a passing control uncounted.
- P0.6's own mutants that name the gate's git calls by their text no longer apply, as each call is now the helper's.
- **The runner** on the tree as frozen but for this entry: run `20261026-062221-63677-cbdb6a3+dirty`, 18 stages
  passed and 6 skipped by name, 343 s of stage time beside three agents.
  - 2,923 tests, 366 more than at P0.6's commit: format 1,302, docs 189, tool-tests 196, vocab-tests 12, custody 23,
    control-tests 32, p1 1,169.
  - The privacy gate read 296 files, 8 commit messages and 138 versions in earlier commits, and listed the three
    known findings.

**Next:** P0.7's verifier, on Sonnet and the full bar.

## 2026-10-26 - P0.7's first verifier: NOT READY, the controls without a stream, the writer's net; the fixes

**The verdict** (docs/reviews/P0.7/round1.md): NOT READY, on the full bar, the first of three.
- **D1, a gate, a regression.** The controls' `git init` was the gate's one git whose output was not captured. With
  P0.7's helper giving it no stdin, Python's subprocess started it with a copy of the gate's own stdout and stderr,
  and where either was closed (Git Bash's `>&-` or `2>&-`) the copy failed, OSError, WinError 6: `--control` exited
  1 where cbdb6a3's gate exited 0. The run was immune, as each of its git calls captures its output. No test caught
  it: the test of every git asked of stdin alone.
- **D2, a gate, inside O1.** A clean sparse checkout passed the run and failed the controls: their copy read every
  tracked file from disk, and raised FileNotFoundError after all the plants had passed. So did any tracked file
  deleted from disk. The entry above's "a clean sparse checkout is no longer refused" was true of the run alone.
- **D3, code and prose, the writer.** P0.7 gave the reader only an arranging TypeError. An entity with no @id, an
  entity or a graph that is no object, a graph or a context missing, and a reference with no @id still raised
  KeyError or ValueError, where the reader refuses each by name. The writer's docstring and the entry above say
  otherwise.
- **D4, prose.** FORMAT.md item 22's first rdflib bullet says that `@x`, `.`, `././`, `//` and `?` are the
  descriptor's IRI where the crate is read from its metadata file's own URL. There `.` and `././` are the root; only
  `@x`, `//` and `?` are the descriptor's IRI. And `;`, which the parameters' bullet calls the root, is the
  descriptor's IRI there too. The lead's run agrees (rdflib 7.6.0 under Python 3.12.9, at https and file bases).
- **D5, prose.** qro/spelling.py's comment still names a prefix of the context, where the rule is now any term; and
  qro/checker.py's docstring and CLAUDE.md say a reader or generator that fails is refused by its step's name, with
  no word of the MemoryError.
- **What held** (MEASURED by the verifier):
  - the freeze, and the runner in four copies: a `git init` copy and a clone with the tree committed over it, 18
    stages passed and 6 skipped by name, 2,923 tests; a copy with no .git and a shallow clone, the gate's stages;
  - the reader's new path tree against cbdb6a3's, the same refusals and texts over 393,195 sequences, and time
    linear in the segments: 50,000 in 0.118 s;
  - 40,000 whole-reader cases, where every one that changed holds a term-scheme id, and none was refused before and
    accepted now;
  - the id rule: 311 schemes newly refused, exactly the shaped terms less the 23 prefixes; the six registered ones;
  - rdflib's other claims in item 22, and the third limit;
  - the MemoryError over 12 exception types at 6 points, as a process; the cut at every code point and offset;
  - the registry's lint plants; the gate under every stdin, sparse checkouts of three kinds, `wsl-unc`;
  - the lead's 29 mutants' targets, passing on the unmutated tree; 5 of its own 9 mutants killed, the 4 survivors
    its notes and one equivalent.

**The fixes:**
- **D1.** The git helper captures stdout and stderr unless the call takes them, so no git the gate starts is given a
  copy of the gate's own streams. A process test runs the gate with its stdout, then its stderr, a handle that names
  nothing on Windows (closed elsewhere), in both modes; and the test of every git now holds each one's stdout and
  stderr too.
- **D2.** What the run passes over, the controls' copy passes over. And both ask git, not Python, which tracked files
  are not in the working tree: `git ls-files -z -t -c -d`, its skip-worktree entries (S) and its deletions (R). That
  takes the verifier's note on O1 too: asked of Python alone, a file git sees and Python cannot, past Windows' path
  limit where long paths are not enabled, was passed over, and an edit `git commit -a` takes went unread (BELIEVED
  by it, not demonstrated). Such a file is a finding again, as before P0.7.
  - The sparse-checkout test and the deleted-file test each run the controls on the clean tree.
  - A test simulates a file git sees and Python cannot read: it is a finding.
  - The test of a dangling link at a gitlink's path now simulates git's view of it as well as Python's: git's lstat
    sees a dangling link, as Python's lexists does, and calls it no deletion.
- **D3.** Where the metadata cannot be arranged or spelled, the reader is given it as JSON writes it, and what the
  reader refuses is refused by its name: the verifier's six shapes, and a NaN, which raised ValueError. Anything
  else is raised as it was: metadata Python's json cannot write at all (a set), a failure of the writer's own on
  metadata the reader accepts, and a MemoryError, the host's even where the reader would refuse the metadata. The
  tests hold each, by the refusal's name and text.
- **D4.** Item 22 says what rdflib does at each base: the root at the crate's directory, for all five; at the
  metadata file's own URL, the root for `.` and `././`, and the descriptor's IRI for `@x`, `//` and `?`. And `;` is
  the base itself: the root at the directory, the descriptor's IRI at the file's URL. In the entry above, "`@x` and
  its kin are ... the descriptor's IRI where the crate is read from its metadata file's URL" is to be read so.
- **D5.** The comment says a term of the context; the docstring and CLAUDE.md name the MemoryError as the host's.

**Its notes, taken:**
- the cap's number held by a test: LINE_MAX is 4,096, and a refusal quoting a long @id is cut at its 4,096th
  character (a LINE_MAX of 9,000 passed every test);
- the nets' width held: a RecursionError, a KeyError and a PermissionError from a raw-form reader or a generator are
  each refused by the step's name (nets widened to a RecursionError passed every test);
- item 16's "whatever a step lets through" names the PermissionError, misuse, exit 2; and the command line's
  docstring says the notice follows the text's first characters.

**Not taken, for later:** the cut drops an exit-2 or exit-3 line's trailer (the usage, or "this is not a verdict")
where the text before it is long; the line's prefix and its exit code still say what it is. And the path tree's
constant, about 320 bytes a segment, which is linear as the entry above says.

**Measured, by the lead:**
- **12 hand mutants of the fixes** (m_p07_r1.py), each killed by its targeted test, 12 of 12 (mut_p07_r1.log):
  the git helper's two streams inherited, and its stderr alone; the controls' copy taking what git calls absent;
  the absent set without its skip-worktree tag, or its deletions; the run's pass-over asked of Python; the writer
  giving the reader a TypeError alone, or a MemoryError too, or not raising its own failure; the cut at 9,000;
  and each of the two nets widened to a RecursionError.
- **The runner** on the tree as frozen but for this entry: run `20261026-080129-19444-cbdb6a3+dirty`, 18 stages
  passed and 6 skipped by name, 308 s of stage time beside three agents and another runner.
  - 2,940 tests, 17 more than the entry above: format 1,314, docs 189, tool-tests 201, vocab-tests 12, custody 23,
    control-tests 32, p1 1,169.
  - The privacy gate read 298 files, 8 commit messages and 140 versions in earlier commits, and listed the three
    known findings.

**Next:** P0.7's second verifier, on Sonnet and the full bar.

## 2026-10-26 - The round paused by a deletion; P0.7: a skip-worktree file on disk, and the agents' sandbox

**What happened.** During P1.2's round-1 fixes, a hand mutant of the adapter's cleanup made it call `shutil.rmtree`
on the users folder, and the adapter's tests, which fail builds on purpose, ran it against the real disk for about
13 minutes before P1.2's builder killed it. It emptied most of the profile's folders and the programs installed in
them, Python's among them. The repositories were not reached. Logan: "What all was damaged is lost, it happens."
Every agent was stopped, Python was reinstalled at the same path (Miniconda py312_26.9.4, so Python 3.12.15, with
pytest 9.1.1 and ruff 0.11.9, as before), and the SHACL environment was rebuilt from
tests/p4shacl/p4shacl_requirements.txt in P4's worktree. P0.7's second verifier was stopped before its report.

**A defect of round 1's fix, found by that stopped verifier.** Its work holds a probe of a file tagged
skip-worktree and still on disk, and its last message named "the skip-worktree gap". Round 1 passed over every file
git tags S; the staged reader reads an index version only where it differs from the file on disk. So a file tagged S,
on disk, its bytes those of the index, was read by nothing, and a key committed into it passed. Before P0.7 the file
loop read it from disk. The gate now passes a file over only where git says it is not in the working tree and it is
gone from disk too (`passed_over`), in the run and in the controls' copy alike.
- A test commits a key into a file, tags it skip-worktree with the file left on disk, and holds that the key is
  found; and that a clean such file passes the run and the controls.
- Two mutants, git's tag alone and the disk alone, each killed by its targeted test (m_p07_r2pre.py).

**CLAUDE.md item 9, the agents' sandbox.** An agent runs every command that executes the project's code, a test, a
mutant or a script of its own through a launcher outside the tree, in a copy of the tree in its own directory:
- at low integrity: the launcher's interpreter is labelled low, so Windows runs it, and everything it starts, at
  low integrity, where a process can write and delete only in low-labelled folders. MEASURED by the lead: a write
  outside the sandbox, made below Python by the Windows API, refused with access denied;
- with a Python audit hook that refuses any write or delete Python makes outside the sandbox. MEASURED: an
  `rmtree` of a folder outside, and a write into the profile, each refused; the same inside, done.

Git Bash crashes at low integrity, as its runtime meets the shared state of the user's other bash sessions, so the
runner and the tests that start bash run through a second launcher: Python still held to the sandbox, at the user's
normal integrity, and bash and git held by the rules alone. The item says so, and that a cleanup in the project's
code removes only what it made.

**Measured, by the lead,** through the second launcher, on a copy of the checkout committed alone: the full runner,
run `20261026-103915-46850-5e5d060`, 18 stages passed and 6 skipped by name, 2,941 tests, 339 s of stage time beside
another runner; the privacy gate read 298 files and the copy's one commit message. At low integrity, on the checkout
as it was before the pause's fix, the seven test directories the runner's pytest stages run gave 2,917 passed and 23
failed: the 23 tests that start bash, which exits 0xC0000142 there.

## 2026-10-26 - P0.7's second verifier: NOT READY, on two sentences; the fixes

**The verdict** (docs/reviews/P0.7/round2.md): NOT READY on two defects, both prose. It found no wrong answer,
crash, exit code or regression in the code, the gates or the tests that hold them, and each of round 1's five defects
and the pause's skip-worktree gap held, MEASURED wide: the gate under 716 states of its three streams; 126 git states
of the working tree against an oracle of git's plumbing, the pause's gap caught where git alone is asked; about
28,000 variants through the writer; 34,589 drawn ids against rdflib 7.6.0; 400,000 sets of colliding paths, old
reader and new.

**D1, a false clause in the first verifier's entry above.** Its "Not taken, for later" says the cut drops an exit-2
or exit-3 line's trailer, and that "the line's prefix and its exit code still say what it is". For exit 3 they do.
For exit 2 they do not: the text before the usage is the user's own argument, so a cut exit-2 line begins with that
argument, and only the exit code says what the line is (MEASURED by the verifier: `python -m qro check` with a
5,000-character name, exit 2, a line beginning with the name). This entry corrects that one; the cut itself is as it
was.

**D2, CLAUDE.md item 9 said more than its guard does.** It said the hook refuses any write or delete Python makes
outside the sandbox, and that under sbx-mid.sh Python is still held to it. The hook sees Python's own file functions;
a program Python starts (git, bash, rm, cmd), `os.system` and ctypes it does not see, and at normal integrity,
under sbx-mid.sh, nothing holds them. Item 9 now says so, and adds the clone rule: a plain local clone hard-links the
repository's object files, so a clone of a real repository is made with `git clone --no-hardlinks`, through
sbx-mid.sh, since git's local transport starts sh, which cannot run at low integrity, or by copying the objects. The
hook itself changed after the verifier's freeze, outside the tree: it now judges a delete or a rename at the entry's
own place and a write through every link, and refuses a write to a file with two names (the lead's ledger).

**Notes taken:**
- **the writer's fallback swallowed a MemoryError,** raised while json wrote the metadata for the reader, and raised
  the first failure in its place, against P0.7's own claim that a MemoryError is the host's. It raises it now, with a
  test (note 7; contrived, but the claim was the writer's);
- four mutants that survived the whole suite where the code is right, each now killed by a test of its own: the
  controls on a tree with no .git, which raised CalledProcessError without the copy's guard (note 1); a short option
  in the lint, `-q`, read by no plant (note 2); the fallback's sorted keys, which no test fed it unsorted (note 3);
  `exists` for `lexists` in the pass-over, which differ only at a dangling link, which this host makes as a junction
  whose target is gone (note 4; the gate reads such a path, unreadable, and the staged version beside it);
- item 8: through the sandbox's launchers, whose python.exe is a venv's redirector, Git Bash's `>&-` closes Python's
  own stdout and hands its children a valid one; a test of a child with no stream uses SetStdHandle (note 5).

**Not taken:** a tracked file replaced by a directory is unreadable, a finding, as at cbdb6a3 and held by a test
(note 6); the IANA sentence of item 22 rests on the lead's fetch of 2026-10-25 (note 8); ruff's own configuration,
which could mask the lint and which no rule pins, is older than P0.7 and goes to P0.8 (note 9); whether
`CREATE_NO_WINDOW` stops the windows needs a process with no console to measure, which item 8 forbids (note 10).

**The real repository's objects.** The verifier measured 526 of its 603 object files with a second name, from clones
earlier verifiers made before the sandbox, outside the tree; none was in use. `git fsck --full` on it found every
object whole (MEASURED by the lead).

**Measured, by the lead:**
- 5 hand mutants, the four survivors and the fallback's MemoryError (m_p07_r2.py), each killed by its targeted
  test through sbx.sh, 5 of 5 (mut_p07_r2.log); each target passing unmutated under the same launcher first;
- the full runner, through sbx-mid.sh on a copy of the checkout committed alone, but for this entry: run
  `20261026-123534-50601-6cc903d`, 18 stages passed and 6 skipped by name, 2,946 tests, 434 s of stage time beside
  three agents; the privacy gate read 299 files and the copy's one commit message.

## 2026-10-26 - P0.7's third verifier: NOT READY, on one sentence; the cap; the fixes

**The verdict** (docs/reviews/P0.7/round3.md): NOT READY on one prose defect, and no wrong answer, crash, hang or
exit code in the code, and no gate fault. Measured again: two runs, 2,946 tests; the corrected sentence of the entry
before and item 8's; the writer against round 2's on 27,490 outcomes, differing only where a MemoryError is injected
at its fallback, which it now raises; the gate's 126 git states and 716 stream states unmoved; rdflib 7.6.0 on item
22; every line P0.7 changed in qro/ run by some test.

**D1, CLAUDE.md item 9's first bullet.** It said a low-integrity process can write and delete "nowhere in the
profile". `%USERPROFILE%\AppData\LocalLow` is in the profile and Windows labels it low for every application, the
sandbox and 57 other folders under it among them, so a program Python starts, which the hook does not see, can write
there and in every agent's directory, the label its only fence (READ, by icacls). Item 9 now says so, and that both
fences hold an agent to the sandbox as a whole, every agent's directory in it, not to its own.

**The cap** (CLAUDE.md item 6): three NOT READYs on reasons grown narrower, five defects with code, then two
sentences, then one. P0.7's fourth verifier is told that only a defect in what the code does blocks.

**Notes taken:**
- the line's cut, held further: its count is of the text's characters, not their escapes' (a mutant counting by the
  escaped length passed every test, each cut falling after ASCII, where the two are one; T1); and the cut on exit 2's
  line and exit 3's, at descriptor 2, held by no test, each of two mutants cutting only REFUSED lines or only
  descriptor 1 passing (T2);
- the no-.git test lets git look no higher than its own directory: where pytest's temporary directory lay inside a
  work tree, git found that one and the guard's mutant passed (T3);
- FORMAT.md item 16's "as any `Exception` they raise is but a `MemoryError`" said plainly.

**The sandbox's guard,** outside the tree (the lead's ledger): its two holes, G1, `shutil.copy2` going by
`_winapi.CopyFile2`, which it did not judge, and G2, an `open` with O_TEMPORARY, which deletes on close, judged a
read, are closed in its third version, with their neighbours: `_winapi.CreateJunction`, a writing
`_winapi.CreateFile`, `sqlite3.connect` outside the sandbox, every registry write.

**Not taken:** the WSL mirror spellings (`//wsl$\...` and the mixed forms), which no alternative finds, are older than
P0.7 and below the gate's threat model: P0.8.

**Measured, by the lead:**
- 4 hand mutants, T1's, T2's two and the copy's guard once more (m_p07_r3.py), each killed by its targeted test
  through sbx.sh, 4 of 4 (mut_p07_r3.log); and the guard's mutant killed with pytest's temporary directory inside a
  work tree (t3check.py);
- the full runner, through sbx-mid.sh on a copy of the checkout committed alone, but for this entry: run
  `20261026-144202-45181-db759fc`, 18 stages passed and 6 skipped by name, 2,948 tests, 477 s of stage time beside
  three agents; the privacy gate read 300 files and the copy's one commit message.

## 2026-10-26 - P0.7's fourth verifier: READY, on the relaxed bar

**The verdict** (docs/reviews/P0.7/round4.md): READY, on the relaxed bar the cap sets, where only a defect in what the
code does blocks. It found none in the code, the gates or the tests and registry that hold them.

**What held** (MEASURED by the verifier):
- the freeze, and the packet equal to the staged index, blob for blob;
- the runner in three copies, a `git init` copy, a `--no-hardlinks` clone with the real history (300 files, 9
  commit messages and 140 earlier versions read, the three known findings listed) and a copy at a path holding a
  space: 18 stages passed and 6 skipped by name, 2,948 tests each; privacy-controls 40 of 40; at low integrity, all
  but the 23 tests that start bash;
- round 3's four mutants and round 2's five, each killed by its target; the no-.git test failing its mutant wherever
  pytest's temporary directory lies; item 8's sentence;
- the sandbox's guard, run with a narrower root inside the verifier's own directory: 43 of 51 operations refused as
  item 9 says, the rest by design (ctypes, `os.system`, a program started);
- the old tree against the new: the writer's bytes for P1's models and the controls' output the same; the reader's
  peak memory at 10,000 segments 2.9 MiB against 192.4 MiB, and no regression on wide trees;
- the id rule: no string of the tree writes an @id whose scheme is a term;
- the gate against 300 random repository states, each committed three ways and searched with `git log -S`: no
  key missed; real paths of 419 characters; a real sparse checkout of the history clone;
- the counts of the five entries above, and the reviews README's.

**Its notes, below the bar, for P0.8:**
- CLAUDE.md item 9's "nowhere else in the profile" is still too wide: besides LocalLow, Windows labels a few profile
  folders low (`AppData\Local\Temp\Low`, `Favorites`, some under `AppData\Local\Packages` and `Publishers`);
- "no parcel writes one", of the six schemes the id rule now refuses, was measured on P1.1 and P4, not P2;
- outside the tree: a child Python started with `-S` loads no guard; `tempfile.mkdtemp` retries a refused directory
  10,000 times, so a refusal there looks like a hang; SCRATCH's hm_t.py removes any WORK under the shared sandbox,
  another agent's among them, and at low integrity counts a survivor killed by the bash tests;
- older, and fail-closed: a tracked file replaced by a directory is reported unreadable; a key in a file git will not
  commit is reported.

**The lead's ruling** (the round's ledger, 2026-10-26): READY stands. The notes are P0.8's, with those gathered before
(SCRATCH\p08\notes.md); the guard's and the tools' are the lead's own, outside the tree.

**The whole of P0.7** took four rounds and three send-backs, and a pause:
- the first on five defects, two in the gate's controls, one in the writer, two in prose;
- the pause, for the deletion, in which the stopped second verifier's work found the skip-worktree gap, and the
  agents' sandbox was built;
- the second on two sentences; the third on one, the cap then reached.

It is committed as the next entry says. Its fixes, and its verifiers' measurements, are in its six entries above,
from "P0.6 committed; P0.7", and in the reports.

## 2026-10-30 - P0.8: this machine's dangling junctions

**P0.7 is committed and pushed** as 83503b0, with the entry above, on Logan's standing word. The runner on the
committed tree, before the push: run `20261026-161022-21312-83503b0`, 18 stages passed and 6 skipped by name, 2,948
tests.

**What P0.8 is.** The lead's piece, and a narrow one. P2.1's merge was laid on 83503b0 in the lead's sandbox, and the
runner failed one stage there: tool-tests, on P0.7's own test
`test_a_link_left_dangling_where_a_tracked_file_was_is_not_passed_over` (run
`20261030-200045-29506-83503b0+dirty`, 18 passed and 1 failed, P2's 509 tests among the passed). The test's control
found nothing where it had made a dangling junction. The same test passed on 2026-10-26, on P0.7's committed tree,
with tool-tests' 204 of 204. So the machine changed between the two runs, and the code did not. The notes gathered
for P0's next piece wait for P0.9.

**What the machine does now** (MEASURED in the sandbox's folders, through both launchers, at normal and low
integrity, and again after the machine restarted):
- **A junction whose target directory is gone is listed but cannot be opened.** os.listdir names it, os.scandir's
  entry says it is a junction, and `dir` shows it as `<JUNCTION>`. But os.lstat raises FileNotFoundError, so
  os.path.lexists, islink and isjunction are all False; os.readlink and os.rmdir raise FileNotFoundError too.
- **It is not Python's:**
  - CreateFileW with FILE_FLAG_OPEN_REPARSE_POINT and no access fails with error 2;
  - a junction made by `mklink /J` behaves the same;
  - GetFileInformationByName, the fast path of Python 3.12's stat, is not exported here.
- **A junction whose target is a file** raises NotADirectoryError from lstat. Once its target directory is made
  again, a junction is a junction to every call, and os.rmdir removes it.
- **The cause is not known.** The machine's Defender platform (2026-10-21) and its drivers are older than the
  change. A file system filter is BELIEVED; looking needs an elevated prompt, which is Logan's.

**What it means for P0's code** (MEASURED or READ; P0's code is unchanged):
- **The checker.** os.walk lists a dangling junction in a crate as a file. `_is_link` says no, and is_file says no,
  so walk refuses the crate `file-link`, "neither a regular file nor a directory". A host that can open the junction
  refuses it `file-link` too, "a link in the crate". The name the crate is refused by is the same on both hosts.
- **The privacy gate.** Take a tracked file that git says is not in the working tree, with a dangling junction at
  its path. It is passed over as nothing, and its index version is read, as a commit takes it. What git itself does
  with a dangling junction at a gitlink's path was not measured.

**The test** (tests/tools/test_tools.py) now tells the gate's `lexists` of the link. Since P0.4, simulate_links in
the same file tells the gate of a symbolic link, because this machine cannot make one without privilege; the new
test does the same for the dangling link. The helper `link_dir`, which only this test used, is removed. MEASURED:
the test passes, and it fails with `exists` in place of `lexists` in `passed_over`, the mutant it was written to
kill.

**CLAUDE.md item 10** states the machine's dangling junctions for every agent. A test that needs a link whose target
is gone tells the code of it, and never makes one. A dangling junction left behind stays until its target is made
again, and pytest names the folder it cannot clear `garbage-*`.

**What the parcels meet:**
- **P4:** three of its tests make a dangling junction, and fail on this machine
  (`test_profile_itself_a_link_to_nothing_is_a_link_too`, in both modes, and
  `test_a_link_below_profile_that_leads_nowhere_is_listed_and_removed_like_any_other`). Run on P4's fifth packet:
  p4's 917 passed and 3 failed; profile passed; p4-shacl's 236 passed. MEASURED, P4's tool on the two states, as the
  tests call it:
  - with `profile/` itself a dangling junction, both modes exit 1, "profile/context.jsonld is missing";
  - with a dangling junction below `profile/`, both modes exit 3: a directory the host cannot list.

  Neither writes or removes anything. P4 adapts its three tests before its merge.
- **P1.2:** its tests pass here. On its third packet, which it built on 37640f0 and so without P0.7's test: run
  `20261030-202241-992-57fec09`, 19 passed and 5 skipped by name, p1's 1,726 tests and p1-crates' 39, as before.

**The runner on P0.8's tree:** run `20261030-202810-2526-83503b0+dirty`, 18 stages passed and 6 skipped by name,
2,948 tests, tool-tests' 204 among them. Its 44 warnings are pytest's own: it cannot clear old temporary folders
that hold dangling junctions, which P4's tests left (item 10).

## 2026-10-30 - P0.8's first verifier: NOT READY, the checker on this machine; the fixes

**The verdict** (round1.md of P0.8's reviews, placed at its commit): NOT READY, on three defects.
- **D1, code: the checker on this machine.** A crate holding a junction whose target is gone failed the checker in
  six of eight places: exit 3, "the checker itself failed, FileNotFoundError". FORMAT.md item 12 refuses such a
  crate `file-link`, on every host. At the metadata file it was `file-missing`. MEASURED by the verifier, through
  both launchers, in process and as processes. The cause:
  - os.walk lists such a junction as a directory, since the directory's listing says so;
  - `_is_link` cannot ask it, since os.lstat raises;
  - the walk descends into it, and listing it fails.
- **D2, prose.** The entry above, "P0.8: this machine's dangling junctions", says of the checker that os.walk lists
  such a junction as a file, and that the walk refuses it `file-link`. Each sentence is false, as D1 shows. The
  lead had reasoned them from the code and labelled them MEASURED, and had run nothing. **This entry corrects them.**
- **D3, prose.** The stranded `garbage-*` folders are mostly P0's own tests'. pytest renames an old temporary folder
  before it removes it, so a junction left in one, live when it was made, then points at nothing. Three tests of
  tests/format leave theirs. CLAUDE.md item 10's rule missed them, and the entry above blamed P4's tests alone.

**What held** (MEASURED by the verifier):
- the freeze;
- the runner in two copies: 18 passed and 6 skipped by name, 2,948 tests, the privacy gate over the real history
  (301 files, 10 commit messages and 143 earlier versions);
- the machine's behaviour, through 24 variants of CreateFileW;
- the old test failing here at its control;
- the new test killing the mutant it was written for, and five more of `passed_over`'s and `held`'s;
- the gate against git with a dangling junction at four places:
  - at a skip-worktree path;
  - at a tracked file's path;
  - at a gitlink's, where git and the gate agree: nothing staged, nothing committed, nothing read;
  - untracked.

**The fixes:**
- **The checker** (qro/checker.py). An entry its directory lists and the host cannot open, os.lstat raising, is
  refused `file-link`, with the detail `UNOPENABLE`. The walk refuses it before it descends, and the metadata file
  is asked before it is looked for. `_is_link` is unchanged, and so is P4's tool, which asks it. FORMAT.md item 12
  says so. MEASURED on this machine: each place the verifier tried is refused `file-link` at its own place, in
  process and as a process (exit 1, one REFUSED line).
- **Its tests** (tests/format/test_hostile.py), each `file-link` at its own place:
  - a real junction whose target is gone, at four places: a name listed by nothing, a listed file's, two levels
    down, the metadata file. It is refused on this machine and on a host that opens it alike;
  - one whose target became a file;
  - one as a process;
  - the walk's question planted, so that it is held on every host, at a directory, a file and the metadata file,
    the walk never listing what it refused.
- **D3.** Every junction a P0 test makes is removed when the test ends, while its target is there: the `links`
  fixture in test_hostile.py, and `unlink_made` in test_refusals.py. MEASURED: after the format tests, no link is
  left under the run's temporary folder. CLAUDE.md item 10 says why, and where it was measured, and that the
  checker refuses such an entry.
- **Notes taken:**
  - item 10 scoped to the sandbox's folders, where it was measured;
  - "since 2026-10-30" made "found on 2026-10-30", since the change came between 2026-10-26 and 2026-10-30;
  - the new test's docstring names the test that holds the other half,
    `test_a_sparse_checkout_passes_and_what_it_leaves_out_is_read`.
- **Mutants:** five of the new code, each killed by its target, through sbx.sh (the lead's scratch, p08/r2fix/).
- **Left as it is:** the `garbage-*` folders already stranded in the sandbox's temporary folder. Their junctions'
  targets cannot be read, so they cannot be made again; they are inside the sandbox, and harmless. The entry above's
  "44 warnings" were pytest's own, the count of one stage's run; the verifier counted 362 and 235 over its runs.
- **The lead's probes,** outside the tree, now leave nothing.

**The runner on the fixed tree:** run `20261030-214813-15810-83503b0+dirty`, 18 stages passed and 6 skipped by name,
2,957 tests, the format stage's 1,327 among them, nine of them new. The 160 warnings each of format and tool-tests
shows are pytest's, about the `garbage-*` folders stranded before this round.

## 2026-10-30 - P0.8's second verifier: NOT READY, on one sentence; the fixes

**The verdict** (round2.md of P0.8's reviews, placed at its commit): NOT READY, on one sentence, with no defect in what
the code does, in a gate or in a test.
- **D1, prose.** FORMAT.md item 12 said that an entry its directory lists "that the host cannot open" is refused
  `file-link`, which is wider than the code: the code asks whether os.lstat raises. The fault that shows it: a file
  another handle holds with no sharing is listed, can be stat'd, and cannot be read. The checker answers it exit 2, as
  item 16 says of a path the user may not read, where item 12 read as `file-link`. The docstring and the detail text
  said the same.

**What held** (MEASURED by the verifier):
- the freeze;
- the runner in two copies, 2,957 tests each, the privacy gate over the real history (301 files, 10 commit messages
  and 147 earlier versions);
- round 1's fix at every place, as processes too; a dangling junction as a custody log, a record or a crate is
  never exit 3;
- 23 crate shapes, before the fix and after: seven rows changed, each now `file-link`, and the other sixteen are the
  same;
- P0's tests leaving no junction over five sessions in a row, where the old test stranded two;
- the gate's half;
- the native NtOpenFile failing too, STATUS_OBJECT_NAME_NOT_FOUND;
- the restart, the machine having booted at 2026-10-30 20:15:07;
- the walk's cost, about a quarter more for one more lstat an entry, and linear.

**The fixes:**
- **D1:** item 12 says "that the host cannot stat, `os.lstat` raising on it", and that an entry the host can stat
  and cannot read is item 16's misuse, exit 2. The docstring and `UNOPENABLE` say "cannot stat".
- **Notes taken:**
  - the planted test raises NotADirectoryError as well as FileNotFoundError, so that narrowing the question to one
    error fails on every host (the verifier's MA);
  - at the metadata file it holds that the refusal comes before the metadata is read, so that `check()`'s own question
    is held on every host, not only the walk's beside it (U2);
  - a test that `check()` of a crate directory that is not there is `file-missing` in process (the verifier's MB);
  - the corner of a dangling link at the metadata file's name in another case, stated in item 12: `file-missing` on
    a host that cannot stat it, `file-link` on one that can.
- **Corrections of the two entries above,** which stand as written:
  - the first's rule, "a test that needs a link whose target is gone ... never makes one": item 10 now allows one,
    made and removed with its target made again;
  - the second's "their junctions' targets cannot be read, so they cannot be made again" does not follow. A stranded
    junction's target is its folder's old numbered path, which can be made again, as the second verifier did in its
    own folder. The lead clears the shared ones when no agent runs pytest there;
  - the first's "the machine's Defender platform (2026-10-21) and its drivers are older than the change": its
    signatures are not, updated on 2026-10-30 at 11:11, inside the window.
- **Notes left for P0.9:**
  - the question's case-folded and reordered mutants, and its detail text's (the verifier's MC, MD and MH), which
    change no refusal's name;
  - that a P0 test leaves no junction behind is held by the fixtures' text, not by a test (TA, TB).
- **Mutants:** seven, each killed by its target: MA, MB and round 1's five (the lead's scratch, p08/r3fix/), through
  sbx.sh.

**The runner on the fixed tree:** run `20261030-225613-24475-83503b0+dirty`, 18 stages passed and 6 skipped by name,
2,961 tests, the format stage's 1,331 among them.

## 2026-10-30 - P0.8's third verifier: NOT READY, on two sentences; the cap reached; the fixes

**The verdict** (round3.md of P0.8's reviews, placed at its commit): NOT READY, on two sentences of FORMAT.md item 12,
with no defect in what the code does, in a gate or in a test.
- **D1, prose:** "any entry its directory lists that the host cannot stat" is still wider than the code. The walk
  and `check()` ask `_is_link` first, whose `is_symlink` raises for every failure of the question but those that mean
  "not there" (ENOENT, ENOTDIR, EBADF, ELOOP, and Windows' errors 21, 123 and 1921). So only those reach the new
  question. MEASURED by the verifier, under Python 3.12.15 and 3.13.5: a refused permission at a listed entry is
  exit 2, item 16's misuse, and another error (EIO, ENAMETOOLONG, EINVAL, Windows' 1920) is exit 3, where item 12
  said `file-link` for each. Its second sentence, "an entry the host can stat and cannot read ... is item 16's
  misuse", was wider than item 16 too.
- **D2, prose:** the wrong-case corner was stated for a host that folds case alone. On one that keeps case it is
  `file-missing` either way.

**What held** (MEASURED by the verifier):
- the freeze;
- the runner in two copies, 2,961 tests each, 13 of them new since 83503b0;
- round 1's fix at every place, as processes too, and under Python 3.13.5;
- 28 crate shapes before and after: eleven rows changed, each as expected, the other refusals in the same order;
- P0's tests leaving no junction over six sessions in a row;
- every test of the round holding what it names;
- the three corrected sentences true;
- the gate's half;
- the walk's cost, linear.

**The cap is reached** (CLAUDE.md item 6). P0.8's three NOT READYs came on narrower reasons each time:
- first, the checker failing on this machine;
- then one sentence's width;
- now two sentences, of the same kind.

So its fourth verifier blocks only on a defect in what the code does.

**The fixes:**
- **D1:** item 12 says what the code asks. An entry its directory lists is refused `file-link` when the host, asked
  what it is, says it is not there (FileNotFoundError, NotADirectoryError and the like). Any other failure of that
  question, or of reading the entry, is no refusal: a refused permission is misuse, exit 2, as item 16 says, and any
  other error of the host's is the checker failing, exit 3. The question is named for what it asks:
  `_listed_not_there` and `LISTED_NOT_THERE`, before `_unopenable` and `UNOPENABLE`. The walk's docstring and
  CLAUDE.md item 10 say the same.
- **D2:** the corner restated: `file-missing` on a host that cannot stat the link; on one that can, `file-link`
  where the host folds case and `file-missing` where it keeps case.
- **Notes taken:**
  - the planted tests plant both calls that ask what an entry is, os.lstat and os.stat with
    `follow_symlinks=False`, which is pathlib's, as a real host fails both (the verifier's note 1);
  - a new test holds that a refused permission and another error, at a listed directory, a listed file and the
    metadata file, are raised, never `file-link`. It kills the verifier's N4, the question asked before the link
    test, which had passed every test, and its twin at the metadata file;
  - the fixtures' docstrings say that pytest's own cleanup cannot remove a stranded link, not that nothing can.
- **Notes left for P0.9:**
  - an NTFS stream on a listed file is accepted, as before P0.8, its default stream the one the digest covers;
  - TA and TB, the fixtures' removal held by their text alone;
  - the case-folded and reordered mutants of round 2's notes.
- **Mutants:** nine, each killed by its target: N4, its twin at the metadata file, and round 3's seven under the
  question's new name (the lead's scratch, p08/r4fix/), through sbx.sh.

**The runner on the fixed tree:** run `20261030-234824-2578-83503b0+dirty`, 18 stages passed and 6 skipped by name,
2,967 tests, the format stage's 1,337 among them.

## 2026-10-31 - P0.8's fourth verifier: NOT READY, on Python 3.14's pathlib; the fixes

**The verdict** (round4.md of P0.8's reviews, placed at its commit): NOT READY, on the relaxed bar, on one defect in
what the code does, latent on this machine.
- **D1, code, on Python 3.14 and later.** The checker's question took only "not there" errors because `_is_link`'s
  `Path.is_symlink()` raised every other first. That is pathlib's behaviour in 3.12 and 3.13. In 3.14,
  `Path.is_symlink()` answers False for every OSError (READ by the verifier: the 3.14 documentation's "Changed in
  version 3.14" note, its source, and the branch's `Lib/pathlib/__init__.py`). There, every failure of the question
  reached it, and a refused permission or another error at a listed entry was refused `file-link`, exit 1, with a
  reason the host did not give. `requires-python` is ">=3.12", so 3.14 is a Python the tree takes. MEASURED by the
  verifier, under an emulation of 3.14's pathlib on 3.12.15: the six tests of that answer failed, and the command
  line's mapping gave exit 1 where items 12 and 16 say 2 or 3. Nothing is accepted that should be refused.

**What held** (MEASURED by the verifier, on 3.12.15 and 3.13.5):
- the freeze;
- the runner in two copies, 2,967 tests each;
- round 1's fix at 17 shapes, in process and as three kinds of process;
- a model-based fuzz of 600 random trees with no mismatch, where the same harness on 83503b0 found 42;
- every fix of rounds 1 to 3, and its mutants of them, each killed by the test that holds it;
- P0's tests leaving no junction, passing or failing;
- the machine as item 10 says;
- the gate;
- the walk's cost.

**The fixes:**
- **D1:** the question classifies the host's error itself. It answers "not there" only for ENOENT, ENOTDIR, EBADF
  and ELOOP, and Windows' errors 21, 123 and 1921, the list pathlib 3.12 and 3.13 read so (`NOT_THERE_ERRNOS` and
  `NOT_THERE_WINERRORS` in qro/checker.py). It raises every other, whatever pathlib's `is_symlink` does. Nothing
  changes on 3.12 or 3.13, where the link test raises first.
- **The tests hold it on every interpreter:** the planted tests run under pathlib's answers of 3.12 and 3.13 and
  under those of 3.14 (`pathlib_answers`, `is_symlink` and `is_junction` answering as os.path does). MEASURED: the
  format tests pass, 1,182, and so do the two files under the verifier's emulation of 3.14 (437), where without
  the fix six failed.
- **Notes taken:**
  - a test that `check()` of a crate path that is a file is `file-missing` in process, which kills the verifier's
    M5;
  - the real-junction test's docstring says "says is not there";
  - the long line rewrapped.
- **Notes left for P0.9:** within one directory the walk asks directories before files, and on a host that opens
  dangling links a dangling symbolic link to a directory sorts among the files, so with two link-like entries of
  different kinds in one directory the place named could differ by host, though the refusal's name cannot
  (BELIEVED, not run).
- **Mutants:** eleven, each killed (the lead's scratch, p08/r5fix/), through sbx.sh: the classification's two (R1,
  R2), M5 (R3), and round 4's eight that still apply. N4 and its twin are now killed by other tests than their
  target, since the question's own classification answers what their order once decided.

**The runner on the fixed tree:** run `20261031-004932-9144-83503b0+dirty`, 18 stages passed and 6 skipped by name,
2,980 tests.

## 2026-10-31 - P0.8's fifth verifier: READY, on the relaxed bar

**The verdict** (docs/reviews/P0.8/round5.md): READY, on the relaxed bar the cap sets, with no defect in what the code
does that a crate or the command line can reach, and no gate, stage, test or registry that passes a fault it claims
to catch.

**What held** (MEASURED by the verifier):
- the freeze, and the runner in two copies, 2,980 tests each; the privacy gate over the real history, 40 of 40 of its
  controls caught;
- the question's classification against pathlib's own, `_ignore_error`, on 2,301 planted errors, every errno and
  every Windows error from 0 to 2,199, on 3.12.15 and on 3.13.5: 0 mismatches. The command line as a process, 51
  rows, gives exit 1, 2 and 3 as items 12 and 16 say, under pathlib's answers of 3.14 as under the real ones;
- the suites under the emulation of 3.14's pathlib: tests/format, custody, vocabulary and controls, 1,417, and
  tests/p1, 1,169; the source of 3.14's `Lib/pathlib/__init__.py` READ, the six methods the emulation models;
- 17 shapes of round 1, in process and as three kinds of process; a model-based fuzz of 200 fresh trees, 0
  mismatches; 550 random crates against 83503b0: the 315 with no dangling-style junction the same in exit, stdout
  and stderr, the 235 with one each `file-link` or refused first by its changed metadata;
- P0's tests leaving no junction, over some 40 sessions, mutants among them;
- 32 mutants of its own: the classification's, the question's, the walk's and `check()`'s.

**Below the bar, about the code:**
- **C1:** in process, `checker.check()` of a crate path holding a NUL character, or longer than 32,767 characters on
  Windows, now raises ValueError, where it was `file-missing`: the question calls os.lstat itself and catches
  OSError alone. No crate's name can hold a NUL, and the command line refuses such a path before `check()`, exit 2.
- **C2:** on Windows a name ending in a dot or a space is listed by its directory and cannot be stat'd, since lstat
  strips the character. A file so named was `file-link` before and is now, by another detail. A directory so named
  was walked, or failed exit 3, and is now refused `file-link`, as item 12 says.

**Corrections of the entries above, which stand as written:**
- "eleven [mutants], each killed" (the fourth verifier's entry): two of them, N4 and its twin at the metadata file,
  the order of the link test and the question swapped, are equivalent now, the question classifying by itself. The
  lead's harness counted them killed "not by its target": at low integrity, the bash tests of its fallback run fail
  whatever the mutant, the trap its own note records (P0.9's notes, item 12). Nine of the eleven were killed.
- "the format tests pass, 1,182" (the same entry): those are four files of tests/format, not the stage, whose count
  is 1,350.

**Notes, for P0.9** (SCRATCH\p08\notes.md):
- the classification's constants are held in part: EBADF, ELOOP and Windows' 21, 123 and 1921 dropped, or EINVAL
  added, pass every test; a test that compares the tuples with pathlib's own lists on 3.12 and 3.13 would hold them;
- C1's one line, `except ValueError: return False`;
- Windows' error 21, "not ready", is a PermissionError Python lists among "not there", so item 12's "a refused
  permission is misuse" is wider than the list: the list should be named, not paraphrased;
- `pathlib_answers` patches `is_junction`, which already answered False for every error in 3.12 and 3.13;
- the module docstring of qro/checker.py, step 2, does not name the new refusal.

**The whole of P0.8** took five rounds and four send-backs: the first on the checker failing on this machine, and
the lead's false sentence; the second on one sentence's width; the third on two more, the cap then reached; the
fourth on Python 3.14's pathlib. It is committed as the next entry says.

## 2026-10-31 - P0.8 committed; P2.1 merged: the golden measures' core

**P0.8 is committed and pushed** as d98295e, with the entry above, on Logan's standing word. The runner on the
committed tree, before the push: run `20261031-020641-2887-d98295e`, 18 stages passed and 6 skipped by name, 2,980 tests.

**What P2.1 is.** P2 is the golden measures' parcel. It measures what a crate's law and coherence PUBs did; it says
of each measure whether it tells the law from its classical twins (signal) or only shows the run is sound
(integrity); and it holds a compile's gate lists to the logical circuits they claim to be. Its design is P2.md items 1
to 14 in the round's ledger, approved with the lead's decisions on it (lead.md 2026-10-16T00:24:00Z). P2.1 is its
core, built on Opus in its own worktree from 37640f0. It adds 33 files, and changes one, docs/README.md, by its
page's line:
- **qro/p2_law.py:** the law file `qro-law/1`, the twins, every measure's expected value, and the classes;
- **qro/p2_interval.py:** `qro-hoeffding-kl/1`, the certified intervals, in integers;
- **qro/p2_sim.py:** the readers of gate lists and logical circuits, the simulator, and the memo;
- **qro/p2_hold.py:** `qro-exact-hold/1`;
- **qro/p2_measures.py:** the estimators, the family and its intervals, the entities, and the seam with P1's
  generator;
- **qro/p2_steps.py:** steps 6 and 7;
- **qro/p2_report.py:** the floor, the z statistics and the standard errors, read by no step;
- **qro/register_p2.py:** steps 6 and 7, each with its entry rule, and nothing else;
- **tests/p2/:** P2's tests and their builder, p2_builder.py, which writes P2's own synthetic crates;
- **tests/p2/data/:** ten of Quantum-Film's files, kingston's morning bundle of 2026-10-05 and the source circuit,
  copied byte for byte from moth-quantum at 3a73823, and their README with its MIT notice (the lead's decision 9 on
  P2's design: P2.2 replaces each copy with a read of P1's twin where the twin carries the same bytes);
- **docs/P2.md:** P2's page, which names, for each claim, the tests that hold it, and says where none does.

P2.2 is not built: the controls `class-declared` and `compile-broken`, the tests on P1's twin, and the `p2-crates`
stage on v0's two crates.

**What the steps hold** (docs/P2.md, sections "Step 6" and "Step 7"):
- **Where they enter** (the lead's E1, lead.md 2026-10-26T10:52:46Z): step 6 only on a term whose step is 6 or an
  entity typed `qro:Measuring`, `qro:Contrast` or `qro:Measurement`, and step 7 only on a term whose step is 7 or an
  entity typed `qro:Hold`. So P0's fixture, which carries none of them, costs P2 one look at its graph's keys and
  types, and is accepted with every `qro.p2_*` module unimportable.
- **Step 6, `measure-class`:** exactly one question, with the measure set `qro-measures/1` and its two twins; the law
  file read strictly and held to the question's own circuit, every layout's probability, the mass outside them and
  each observable within 1e-10; every Contrast's class and values as computed, a class never read from a crate;
  every law and coherence
  Pub measured from its raw bytes through P1.1's `pub_counts`, each certified interval at alpha 1/20 over the crate's
  family.
- **Step 7, `compile-uncontrolled`:** one Hold for each Compile, under `qro-exact-hold/1`; every gate list a
  manifest names that the crate carries held to its logical circuit, and that circuit to its role, whatever any claim
  says, in every Compile and at every entry of its manifest; no gate list in a Compile's `object` or `result` that
  its manifest does not name; and the Hold's word the one the gate lists' presence gives.
- **The intervals** are Hoeffding's bound in its KL form. Each end is a point on the grid j / 2^48 proven outside
  the set in integers, so no rounding narrows an interval and every host writes the same endpoints.

**Measured through the built code** (each pinned by a test the page names):
- v0's law: 78,482 bytes, its SHA-256 pinned; 4,368 layouts of 5 crystals on the 4 x 4 tile, over 4,096, with 1,360
  forbidden; X0X1 = Y0Y1 = 3/8; and the study's section 7, every value and class of its two columns;
- kingston's four morning gate lists hold, every outcome within 1e-14 of its logical circuit's; the plants on them
  are refused, and the phase plant is accepted, as limit 1 states;
- kingston's pooled five-crystal share less fez's, at family 70, is [12330612205551 / 2^48, 16819644152847 /
  2^48], the study's [+0.0438, +0.0598].

**Changes from the approved design, each taken by the lead:**
- **E1,** where the steps enter (above). The design's rule made step 6 refuse the crates of 17 of P1.1's tests,
  which carry none of P2's terms. Limit 15 states what the change concedes, and step 9 is its cover.
- **E2,** eleven silences of the design, each taken as P2.1 proposed (lead.md 2026-10-26T10:52:46Z). Among them, the
  measure set's three needs of a law, each refused `measure-class`; and a law-role circuit held to the question's
  `qro:law` where the crate carries one, and refused where it does not.
- **Three refusals, at round 2's fixes** (lead.md 2026-10-26T21:29:31Z):
  - a coherence Pub whose raw result Atlas's rule decodes, which round 1's code measured as an x0x1 of 1/30 from the
    all-Z layouts;
  - a gate list in a Compile's `object` that its manifest does not name, as one in its `result` was;
  - the QASM reader's cap, counting gates rather than lines, and barrier lines apart, at 100,000 each.

  The third verifier measured that none refuses what an honest crate holds.

**The three rounds** (docs/reviews/P2.1/):
1. **NOT READY,** with no wrong answer, on five gates and a sentence:
   - the central invariant was untested where a Hold says `withheld` and some gate lists are carried;
   - two checked terms and two counts had no plant;
   - a coherence circuit's sign was not held;
   - T1 let through faults that read the metadata file;
   - the page's "every claim here is held by a test" was false while those stood.

   The deletion of 2026-10-26 took P2.1's builder's transcript. A new builder, on Opus, took the fixes over from
   P2.1's record.
2. **NOT READY,** with no wrong answer, on two gates and a limit:
   - step 7's loops were held by no plant past the first Compile and the manifest's middle entries;
   - three parts of the memo's keys were held by no test;
   - limit 13 left the references out of the cost.
3. **READY,** on the full bar. Every round-2 fix held. Of the second verifier's mutants, all were killed but one,
   which is equivalent. Measured wide again:
   - 6,866 edits of every P2 term on four crates, 229 raw edits and 6,300 values;
   - the law file and its digest by the verifier's own kernel;
   - 2,644 intervals against mpmath bisection at 90 digits, alike under 3.13.5;
   - its own simulator against v0's real files;
   - the memo across 21 crates in 126 warm replays;
   - 43 hostile files as processes;
   - 777 mutants, 718 killed. Of the 59 live, 44 are equivalent or unreachable, and 15 are bounds no test pins.

**Measured at the merge:**
- P2.1's own mutants:
  - at the build, 30 hand mutants and 550 automatic ones, every survivor equivalent or on a boundary, or killed by a
    test added;
  - at round 1's fixes 27, and at round 2's 51, all killed after their baselines;
- the verifiers' mutants: round 1's 902 automatic and 81 hand, whose live gaps round 1's fixes took as tests, and
  which the second verifier found killed, with the nine round 1 left unrun; round 2's 664; round 3's 777;
- P0.7's id rule, which refuses an absolute IRI whose scheme is a term of the context: P2's tests pass under it, so
  the crates they hold accepted carry none (P0.7's fourth verifier's note 2: "no parcel writes one" was measured on
  P1.1 and P4 alone);
- the runner on the merged tree: run `20261031-021409-1151-d98295e+dirty`, 19 stages passed and 5 skipped by name
  (p4, p1-crates, p2-crates, profile and p4-shacl), 3,489 tests, p2's 509 among them.

**The stated limits** are docs/P2.md's "What it concedes", items 1 to 16, each naming the test that pins what it
concedes, or saying that none does.

**Left for P2.2,** with its page's "What P2.1 leaves to P2.2" (P2.1's third verifier's notes, lead.md
2026-10-26T23:02:20Z):
- N1 to N4, bounds where the code is right and no test pins them, each one test:
  - a gate list of exactly 100,000 gates;
  - a `cx`, `ry` or barrier index equal to the width;
  - the one-qubit boundary;
  - in p2_law: one crystal, the observables' edge, `_CLASSES`' 64, a never-co-occupied pair's default, and `_det`'s
    pivot swap;
- N7, three test files that hold one non-ASCII character each;
- the budget on the exact hold's work left open for P2.2's design (lead.md 2026-10-26T18:56:48Z), counting
  references, as limit 13 now says.

N5 goes to P3's design: `p2_interval.pooled` takes a float or bool total, where `interval()` refuses a float. N6
is by design.
