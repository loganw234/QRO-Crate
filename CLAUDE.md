# Working on QRO-Crate

Short, and only things that are non-obvious AND have already cost time. The
README says what this project is; this file says what will bite you.

## Start here: one command answers "does it still hold?"

```
bash verify/run.sh --budget quick   # ~70 s idle (2026-10-16), ~170 s beside other work (2026-10-19): all
                                    #   but study-plants, privacy-controls, instruments, p1-crates, p2-crates
                                    #   and p4-shacl
bash verify/run.sh                  # ~125 s idle (2026-10-16), 150 to 365 s beside other work (2026-10-19):
                                    #   every stage; instruments, p1-crates and p2-crates skip BY NAME without
                                    #   QRO_MOTH_ROOT, p4-shacl without QRO_SHACL_PYTHON
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
- **pytest in a stage reads pyproject.toml and nothing else:** no
  conftest.py, no other configuration file, and a `pytest_plugins` line is
  refused before pytest starts. It enters every directory under tests/
  but `__pycache__` and a virtual environment's, `build/` and dot-directories
  among them. A test class it cannot collect, a test that returns a value
  where it should assert, an assert on a tuple and an unknown mark each
  fail the stage, the tuple only where pytest rewrites the module afresh
  (pyproject.toml says when it does not); a test file outside tests/, or
  tests in a module under tests/ that pytest does not collect, fail the
  registry (P0.1's verifier, rounds 1 to 4; P0.2's, rounds 1 and 2).
  pytest's naming decides what is a test: a helper under tests/ names no
  function `test*` and no class `Test*`. A class so named outside tests/
  that is no test, a `TestStatistic` in qro/ say, sets `__test__ = False`,
  or pytest tries to collect it in each test module that imports it.
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
  11 states the path's, and item 22 the @id's: one spelling of the IRI it
  names, so that the graph the checker holds is the one a JSON-LD reader
  makes, within the limits item 22 states (P0.5).
- **A CHECKED term names its checker step, and a crate carrying a CHECKED
  term whose step is not yet built is refused `step-unbuilt`.** Steps 4 to
  8 are the parcels'. A parcel declares its steps, raw forms, count rules
  and generators in its own module, `qro.register_<parcel>`, which
  `checker.load()` merges (FORMAT.md item 20); never let a crate pass a
  check that does not exist. Your step runs on every crate, P0's fixture
  among them, so it must accept one that carries none of its terms.
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
  on a crate is refused by its step's name (FORMAT.md item 16), but for a
  MemoryError, the host's, which is the checker failing, exit 3: a bug in
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
   commit, UTF-16 included, every blob of HEAD's history and every commit
   message, and lists any binary file it could not read by name. A home
   path, an address or a key committed and then deleted is still pushed, so
   the gate fails on it until that history is rewritten, before a push; once
   pushed and judged no secret, its blob is named in the gate's KNOWN (P0.6).
   So a test's fixture shaped like a key, a CRN, an address or a home path is
   built at run time, in pieces, as the gate's own plants are
   (`"QISKIT_IBM_" + "TOKEN="`), never written whole in a file (P0.1's
   verifier, round 4, N8).
4. **Real QPU work is Logan's word, and is held until the M1 prototype
   exists** (study QRO-0, section 13). Read-only use of the key is cleared.
5. **Nothing is committed or pushed without Logan's word.**
6. **Verifier send-backs have a loose cap** (Logan, 2026-10-15). After three
   NOT READY verdicts whose reasons grow more menial, the next verifier is
   told that only a defect in what the code does blocks. Prose, test gaps
   where the shipped code is right, and other non-code findings become
   notes the lead takes afterwards. The lead may keep sending back past the
   cap where the findings are real, and says why in the ledger. P0 took six
   rounds before this rule; docs/VALIDATION.md has them.
7. **Parcels built at once keep out of each other's files** (study QRO-0,
   section 13; P0.1, after its verifier's round 1, D3). A parcel's own:
   - its checker code, registered in `qro.register_<parcel>` (above);
   - its plants, in its own plants_<parcel>.py in controls/, never in
     controls/registry.py;
   - its tests, in tests/<parcel>/, every file named `test_<parcel>_*.py`
     or `<parcel>_*.py`, so that no two parcels' names meet;
   - its ledger notes, in its own file outside the worktrees, which the lead
     merges into docs/VALIDATION.md;
   - its own page, docs/<parcel>.md, and that page's one line in the index,
     docs/README.md, added in the same change: check_docs fails a page with
     no line and a line with no page, so only the parcel can add both (P0.3).

   The lead's, which a parcel asks for:
   - a vocabulary row;
   - a stage (P1's, P2's and P4's are already in verify/run.sh, with
     p1-crates, p2-crates, profile and p4-shacl, each skipped by name until
     its directory or tool exists), and with it a tool's, and a new
     top-level directory's place in the lint line;
   - a command of the command line;
   - any other document directly under docs/;
   - the names of its modules under qro/, given in its approved design, so
     that two parcels' never meet;
   - any other outcome for the controls' run than refused by a name or
     accepted: P3's and P5's rows that state or keep, and `joint-omission`,
     refused with no name.

   The generated pages never say which controls are built, so a plant
   changes none of them.
8. **A process with no console opens a window for each console program it
   starts** (Logan, 2026-10-26: P0.6's fourth verifier ran the gate under
   pythonw.exe, and its git calls flashed open by the dozen). Never run the
   gate, git, the runner or pytest under pythonw.exe, a detached process or
   a new console; for a closed stdout, use Git Bash's `>&-`. The gate's own
   git calls take no window and no stdin (P0.7). Through the sandbox's
   launchers (item 9), whose python.exe is a venv's redirector, `>&-` closes
   Python's own stdout but hands the programs it starts a valid one: a test
   of what a child does with no stream gives it a handle that names nothing,
   with SetStdHandle, as the gate's tests do (P0.7's second verifier).
9. **Agents run the project's code in a sandbox, and no code deletes outside
   one** (Logan, 2026-10-26: a parcel's hand mutant of its own cleanup ran
   `shutil.rmtree` on the users folder for 13 minutes, and emptied most of
   the profile and the programs installed in it). An agent works on a copy
   of the tree in its own directory under
   `%USERPROFILE%\AppData\LocalLow\qro-sbx`, and runs every command that
   executes the project's code, its tests, a mutant or a script of its own
   through `%LOCALAPPDATA%\qro-crate\sbx\sbx.sh`:
   - at low integrity, where Windows lets a process, and every process it
     starts, write and delete only in low-labelled folders: the sandbox,
     and every other folder under `%USERPROFILE%\AppData\LocalLow`, which
     Windows labels low for every application; nowhere else in the
     profile, the repositories or the system. For a program Python starts,
     which the hook does not see, that label is the only fence (P0.7's
     third verifier);
   - with a Python audit hook, the guarded interpreter's sitecustomize, that
     refuses a write, delete, rename, link, copy or chmod made through
     Python's own file functions outside the sandbox, and a write to a file
     with two names, a hard link, anywhere. It does not see a program
     Python starts (git, bash, rm, cmd), `os.system`, or ctypes.

   Both hold an agent to the sandbox as a whole, every agent's directory in
   it, and not to its own: keeping out of the others' is the rule's work.

   Git Bash cannot run at low integrity, so the runner and the tests that
   start bash (in tests/format/test_cli.py and
   tests/docs/test_stage_registry.py) run through `sbx-mid.sh`, at normal
   integrity, where the hook alone holds anything: a program Python starts,
   and ctypes, are held by nothing there (P0.7's second verifier). A clone
   of a real repository is made there with `git clone --no-hardlinks` (git's
   local transport starts sh, which cannot run at low integrity), or by
   copying its objects: a plain local clone hard-links the repository's
   object files, so that changing one in the clone changes the real one's.
   A cleanup in the project's code removes only what it made, never an
   `rmtree` of a computed ancestor. A subagent's shell starts in the real
   checkout and keeps no `cd`: write only by absolute path, or after a `cd`
   in the same command.
