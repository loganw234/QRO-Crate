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
