# P0.7's second verifier, round 2b: NOT READY, on two sentences

**Verdict: NOT READY.** I found no wrong answer, crash, wrong exit code or regression in the code, the gates or the tests that hold them. Each of round 1's five defects and the skip-worktree gap holds fixed. The two defects are prose: one false sentence in the ledger and one overstatement in CLAUDE.md's new item 9. Restating them needs no code, gate or test change, and then I would call the piece READY.

Labels are READ, MEASURED (script named) or BELIEVED. The scripts are in `<home>AppData\LocalLow\qro-sbx\p07-r2b\mine\`. My notes are in `check\notes.md`. The harness refused a second file, so this message is the report.

## For the coordinator, on hard-linked clones
- **No hard-linking clone.** I did not make one.
  - `git clone --no-hardlinks` and `--local --no-hardlinks` both failed at low integrity and left no directory. Git's local transport starts `sh`, which crashes there.
  - I built `clone\` with `git init` and a plain `cp -r` of the real `.git\objects`, which makes copies.
  - MEASURED (`find -links +1`): 0 of its 616 object files have a link count above 1. The `clone-sparse\` tar copy also has 0.
- **What wrote under `clone\.git\objects`.** Only git itself: my `git rm`, `git add` and `git commit` added loose objects (616 files now against the 603 copied).
  - No probe of mine cut, wrote, truncated or chmod'd an object file there or in the real repository.
  - I ran no gc or repack.
  - READ (grep): the project's own tests never clone the checkout. The ones that damage an object do it in repositories they `git init` in `tmp_path`.
- **Hard-linked clones that are not mine.** MEASURED: 526 of the real repository's 603 object files have a link count above 1.
- **The real repository was untouched during my session.** No file under the real `.git`, and nothing in the top two levels of its working tree, is newer than my first sandbox file.

## What held
- **Freeze.** MEASURED (`freeze_check.py`): all 298 files match `SHA256SUMS.txt`, whose own hash begins `c9a2ec4804bffed7`. The real staged index equals the packet, entry for entry (`git ls-files -s`, read only).
- **Runner.** MEASURED, through `sbx-mid.sh`, in two copies: 18 stages passed and 6 skipped by name in each, 2,941 tests.

  | Copy | Run | Gate read |
  |---|---|---|
  | `git init` copy | `20261026-105138-50795-8930596` | 298 files, 1 commit message |
  | clone of the real repository, packet committed over cbdb6a3 | `20261026-105804-54612-0d21319` | 298 files, 9 commit messages, 140 earlier versions, the 3 known findings |

  - Test counts: format 1,314, docs 189, tool-tests 202, vocab-tests 12, custody 23, control-tests 32, p1 1,169.
  - A real sparse checkout of the clone (146 tracked files off disk) passes `privacy` and `privacy-controls`: 152 files and 146 staged versions read.
- **Low integrity.** MEASURED: the seven pytest directories give 2,918 passed and 23 failed.
  - 21 failures are in `test_stage_registry.py` and 2 in `test_cli.py`, the two files item 9 names.
  - Bash exits `0xc0000142` there.
  - A write outside the sandbox, below Python, is refused with access denied.
  - git runs.

### Round 1's defects and the pause's gap
- **D1, controls without a stream.** MEASURED (`gate_states.py`): stdin, stdout and stderr each in seven states: nul, pipe, file, closed, a handle that names nothing (with and without Python's stream None), and INVALID_HANDLE_VALUE.
  - Run mode on a clean and a keyed repository, plus `--control`: 716 runs, 0 unexpected.
  - With git's streams inherited again, 11 of 30 control runs fail, so the harness can see the fault.
  - Git Bash's own `&lt;&amp;-`, `&gt;&amp;-`, `2&gt;&amp;-` in every combination (`gate_bash_closed.py`): 32 of 32 as wanted.
- **D2, sparse and deleted files; the skip-worktree gap.** MEASURED (`gate_git_states.py`): 126 scenarios against an oracle built from git plumbing only. Result: 0 misses, 0 crashes.
  - States covered: cone, non-cone and sparse index; a file deleted, and deleted and staged deleted; skip-worktree and assume-unchanged each on disk, deleted, edited clean and edited to hold a key; intent-to-add.
  - The run and the controls pass every clean twin.
  - The pause's gap is caught: 7 misses when the pass-over asks git alone. Keeping only the S tag gives 6 more false alarms.
  - 18 further states (nested repository, committed gitlink, gitlink with no directory, unborn branch, linked worktree, autocrlf, odd names, 1,500 skip-worktree files, a file named HEAD) all behave as expected.
  - The gate leaves `.git` unchanged (`gate_readonly.py`).
- **D3, the writer.** MEASURED (`writer_matrix.py`, `writer_matrix2.py`): about 28,000 variants.
  - 60 JSON and non-JSON values at every position of the fixture and P1's two models, plus containers emptied, extended and reordered.
  - 0 flags. A writer whose net is TypeError alone gives 892 flags in 9,289.
  - Where arranging fails, the verdict equals the reader's on the metadata as JSON writes it. Where JSON cannot write it, the failure is raised as it was.
- **D4, item 22.** MEASURED (`r22.py`, rdflib 7.6.0 under Python 3.12.15, sockets refused): every rdflib claim holds at the bases it names.
  - This covers the root and descriptor readings of `@x`, `.`, `././`, `//`, `?` and `;`, the third limit's `.#a:b` and `https://example.org/.#a`, and urllib's eleven schemes.
  - `parse(version=1.0)` still reads 1.1's rule.
  - The central claim holds under 3.12.15 (`sweep*.py`): 34,589 drawn ids at nine bases, the test module's model equal to rdflib on every one, no two distinct ids sharing a node.
- **D5.** READ: the comment and two docstrings now say what is so.

### The rest of P0.7
- **Reader tree.** MEASURED (`diff_reader.py`, `perf_paths.py`): 400,000 colliding path sets give the same outcome and text, old and new.
  - 50,000 segments take 0.105 s and 200,000 take 0.49 s.
  - 10,000 segments peak at 2.8 MB against the old reader's 192.4 MB.
  - No code point folds to or from `/` (all 0x110000 checked).
- **Id rule.** MEASURED: over 300,000 ids it differs from cbdb6a3's only where the scheme is a non-prefix term (58,133 ids).
  - The context has 3,069 terms; 333 are scheme-shaped, plus `qro`; 23 are prefixes; 311 are newly refused. None of those is still accepted.
  - Whole reader against cbdb6a3's package, 26,055 variants: every difference is a term-scheme id, and nothing crashed.
  - BELIEVED: the six IANA schemes. My recall of IANA's lists gives the same six; I did not fetch the registry.
- **MemoryError and the cut.** MEASURED (`cli_matrix.py`, `cut_prop.py`): 18 exception kinds at a raw-form reader, a generator, step 6 and a count rule, run as processes.
  - Every exit code and line is as item 16 says.
  - The cut was tried on 200,000 random cases: never a split escape, the count exact, what is written reads back.
- **Registry.** MEASURED (`lint_rule.py`): 21 lint lines. Every option, a missing or doubled directory, `|| true` and an environment prefix are caught. A `need_env` before a stage that needs no variable is flagged by no rule, as the docstring says.
- **Unintended change.** None found. The three differentials above, and the old gate on the same 126 scenarios, show nothing the new one lacks.
- **Mutation.** The pause's two mutants are killed. Of the lead's other 41 run on the final tree, 37 are killed by their targets and 4 no longer apply, because their text or test name was superseded. The three runner mutants are also killed at mid integrity. Of my 14: 9 are killed by their targets, 4 survive the whole suite (Notes 1 to 4), and 1 is equivalent.
- **Counts in the ledger.** The entries' test counts add up (2,923, 2,940, 2,941), 43 mutants is 17+12+12+2, and the review READMEs' entity counts match the files.

## Defects

**D1 (prose): a false sentence in the ledger.**
- Where: docs/VALIDATION.md, the entry "P0.7's first verifier: NOT READY...", under "Not taken, for later". It says the cut drops an exit-2 or exit-3 line's trailer, and that "the line's prefix and its exit code still say what it is."
- True for exit 3. False for exit 2, where the text before the usage is the user's own argument, so the prefix is that text.
- MEASURED (`long_line.py`): `python -m qro check` with a 5,000-character name gives exit 2 and a line that begins with the name and ends "... (1029 more characters)". Only the exit code says what it is.
- Fix: restate it as the exit code alone for exit 2, or drop the clause.

**D2 (prose): CLAUDE.md item 9 says more than its guard does.**
- Item 9 says the hook "refuses any write or delete Python makes outside the sandbox" and that under `sbx-mid.sh` Python is "still held to the sandbox, bash and git not."
- READ in the guard's own header (`agent-venv\Lib\site-packages\sitecustomize.py`): the hook covers Python's file API events. It says "Not covered by this guard, and left to the integrity level: a program that is not Python (git, bash, rm), and ctypes."
- Under `sbx.sh` the integrity level covers those. Under `sbx-mid.sh` nothing does, so a Python script that starts `rm` or `cmd /c rd`, or calls `os.system` or ctypes, is held by nothing there.
- This is the instruction the fleet runs by after the deletion, so I count it a defect.
- I did not demonstrate the gap. It would mean writing outside the sandbox by a route around the guard.
- Fix: restate the bullet as Python's file API, and say that under `sbx-mid.sh` a program Python starts, and ctypes, are held by nothing.

## Notes (below the bar)

**Test reach, where the shipped code is right.** These are mutants that survive the whole suite; the logs are in `mc\`.
1. **Controls on a tree with no `.git`.** The guard in `_copy` (`if in_git(root) else set()`) is held by no test.
   - Remove it and `--control` on a ZIP-style tree crashes with `CalledProcessError` while the run passes (MEASURED, `work\nogit2`).
   - The real gate passes there, 40 of 40 caught.
2. **The registry's lint rule has no short-option plant.** Its plants are two long options and a doubled name. Change `startswith("-")` to `("--")` and every test passes. The shipped rule catches `-h`, `-q` and `-`.
3. **The writer's fallback sorts keys, and no test notices if it stops.**
   - The writer tests start from a parsed canonical file, so keys are already sorted.
   - MEASURED (`m5_effect.py`): metadata in a generator's key order with an entity lacking `@id` is refused `graph-form` by the real writer, and `spelling` with `sort_keys=False`. All 2,941 tests pass on that mutant at mid integrity.
4. **`os.path.exists` for `lexists` in `passed_over` passes every test.** It differs only for a dangling link, which this host cannot make.

**Prose and other**
5. CLAUDE.md item 8 says "for a closed stdout, use Git Bash's `&gt;&amp;-`".
   - Through the launchers' `python.exe`, a venv redirector, `&gt;&amp;-` leaves Python's stream None but hands children valid Win32 handles. Round 1's WinError 6 does not appear.
   - MEASURED (`gate_bash_closed.py`): the gate with git's streams inherited passes `--control &gt;&amp;-` there, and fails it through the base interpreter.
   - The gate's own tests use `SetStdHandle` and are unaffected. The advice should name the base interpreter or `SetStdHandle`.
6. A tracked file replaced by a directory fails the gate as `unreadable`. A test holds it, and cbdb6a3 does the same.
7. The writer raises RecursionError for values nested about 995 deep and ValueError for an integer past 4,300 digits, where the reader refuses the same content as text (MEASURED, `deep_nest.py`).
   - That fits its docstring's "metadata Python's json cannot write at all".
   - Its fallback `json.dumps` also swallows a MemoryError raised there and raises the first failure instead (READ, contrived).
8. Item 22's IANA sentence rests on the lead's fetch of 2026-10-25, which I could not repeat (BELIEVED, above).
9. The registry cannot see ruff's configuration. A `[tool.ruff]` setting or a `ruff.toml` could mask the lint, and no rule pins it. This is older than P0.7 and not claimed.
10. The git helper's `CREATE_NO_WINDOW` is asserted by a test as a flag only. Whether it stops the windows needs a process with no console, which the rules forbid me to run (BELIEVED, from Windows' documentation). A read-only snapshot of a running background chain (PowerShell) showed each background bash with its own console host and none of its python or git children with one.

## What I did not do
- I did not fetch IANA's registry, run P4's stages, or test on another platform, with long paths past 260 characters, or with symbolic links.
- I did not run anything under pythonw.exe, detached or in a new console.
- I did not re-run the lead's 4 superseded mutants or P0.5's 300,000-id sweep (I ran 34,589 ids). I ran the lead's three mutant files on the final tree, not their original logs.
- I did not demonstrate D2's gap.
- Deviations from the brief:
  - I made four no-op calls of a bare `python3` in my own shell, outside the launcher: an empty program, `--version` and `print(1)`.
  - I used the Bash tool's background mode about a dozen times.
- I left my sandbox directory `p07-r2b` as it is.
