# Working on QRO-Crate

Short, and only things that are non-obvious AND have already cost time. The
README says what this project is; this file says what will bite you.

## Start here: one command answers "does it still hold?"

```
bash verify/run.sh --budget quick   # ~20 s: all but study-plants, privacy-controls and instruments
bash verify/run.sh                  # ~75 s, every stage; instruments skips BY NAME without QRO_MOTH_ROOT
bash verify/run.sh --list           # every stage, with * on what a budget selects
```

`verify/run.sh` is the runner, copied from moth-quantum's. **Reach for it
before hand-running tests.** A pytest stage runs a directory: a new test joins
its stage by where it is saved (tests/<stage>/), and
tests/docs/test_stage_registry.py fails a test file, or a tool's own check,
that no stage runs, as it reads the runner's text; its docstring says what
that reading cannot see.

- **A test that skips inside a stage FAILS the stage**
  (verify/pytest-stage.sh). A skip happens only at stage level, by name.
- **The study has its own gate.** Before every freeze of
  docs/studies/QRO-0.md, run both
  `python -I docs/studies/qro0/check_study.py docs/studies/QRO-0.md` and
  `python -I docs/studies/qro0/check_study_plants.py docs/studies/QRO-0.md`.
  Stale draft numbers recurred four times before the gate existed.

## The format

- **qro/vocabulary.py is the one place a term, a kind, a spelling, a word or
  a refusal is written.** It is P0's: a parcel that needs a term asks the
  lead. `python tools/gen_vocabulary.py --write` regenerates
  profile/context.jsonld and the docs/VOCABULARY.md, docs/REFUSALS.md and
  docs/CONTROLS.md pages; never hand-edit them. Two rules are no term's
  spelling, so they are not in the table: an entity's `@id` and a file's
  path, `id_problem` and `path_problem` in qro/spelling.py. FORMAT.md item
  11 states the path's.
- **A CHECKED term names its checker step, and a crate carrying a CHECKED
  term whose step is not yet built is refused `step-unbuilt`.** Steps 4 to
  8 are the parcels'. Register a step in
  `qro.checker.STEPS`, a raw form in `RAW_FORMS`, a generator in
  `GENERATORS`; never let a crate pass a check that does not exist.
- **The fixture's raw form and generator are registered only by
  `--fixtures`** (`python -m qro check --fixtures DIR`). Without the flag,
  the fixture is refused `step-unbuilt`, by design.
- **One spelling per value.** The reader re-serialises the bytes and
  compares; a second spelling of the same value is refused. Write with
  `qro.canonical.write`, which arranges the graph and refuses what the
  reader would. A pattern that matches digits says `[0-9]`, never `\d`:
  in Python, `\d` matches Arabic-Indic and fullwidth digits too.
- **Exit 1 and a REFUSED line is a refusal; exit 3 is the checker itself
  failing.** A crash inside the checker is never a verdict. Python's own
  failure to start it (no `qro` on the path) exits 1 with no REFUSED line
  (FORMAT.md item 16). And a parcel's raw-form reader or generator that fails
  on a crate is refused by its step's name (FORMAT.md item 16): a bug in
  your reader shows as a refused crate, its detail naming the failure.
- **Test the command line as a process too.** It writes its one line
  unbuffered to the descriptor itself. A buffered write to a closed pipe
  fails only at the interpreter's exit, with exit 120, where no in-process
  test can see it (P0's verifier, round 3, R3-1; tests/format/test_cli.py).

## What bites

1. **A Python heredoc in Git Bash can lose a backslash** (`\\n` arrives as a
   newline, `\\` as `\`), and a long one can fail on an apostrophe. Write
   the script to a file and run the file.
2. **Line endings are part of the bytes.** `.gitattributes` is `* -text`:
   git converts nothing. The instruments' outputs and three records logs are
   CRLF, written on Windows; everything else is LF.
3. **The IBM key never enters the tree.** Connect only through
   moth-quantum's `quantum_film.ibm.account.connect`, after
   `keyleak.refusals(...)`. tools/check_privacy.py refuses each shape its
   ALTERNATIVES table names, each with its own planted control: CRNs, IBM
   ids and accounts, named keys, bearer tokens, JWTs, Moth keys, presigned
   URLs, personal addresses and home paths. It reads every file git would
   commit, UTF-16 included, and every commit message, and lists any binary
   file it could not read by name.
4. **Real QPU work is Logan's word, and is held until the M1 prototype
   exists** (study QRO-0, section 13). Read-only use of the key is cleared.
5. **Nothing is committed or pushed without Logan's word.**
