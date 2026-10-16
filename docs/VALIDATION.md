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
