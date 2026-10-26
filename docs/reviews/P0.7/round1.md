**Verdict: NOT READY.**

P0.7 has one regression in the privacy gate and one half-finished gate fix. It also has a writer that still raises where the reader refuses, and several false or stale sentences. Its core work holds: the reader's path tree, the id rule, the MemoryError change and the line cap each behave as stated, on everything I tried.

**Freeze.** SHA256SUMS.txt begins `13cf185cffa26ed2`. All 296 files of frozen\tree matched at the start and again at the end, and no cache files appeared in frozen\. The tree equals the 20 staged files in the real repository, byte for byte (READ, `git hash-object`). I wrote only under check\ and removed the temp directories my scripts left in the system temp. The real repository still shows HEAD cbdb6a3 with 20 staged files.

**Runner.** `QRO_MOTH_ROOT=… bash verify/run.sh`:

| Copy | Result |
|---|---|
| `git init` copy | 18 passed, 6 skipped by name, exit 0 |
| clone of the real repo with tree\ committed over it | 18 passed, 6 skipped by name, exit 0 |
| no-.git export | `--only lint,docs,tool-tests,privacy,privacy-controls`: exit 0 |
| depth-1 clone | same five stages: exit 0 |

- **Test counts.** They are the lead's: 2,923 tests, 366 more than at cbdb6a3 (2,557 to 2,923, collect-only). Exactly three test ids are gone, and each removal is intended.
- **Privacy gate.** In the clone it read 296 files, 138 history versions and listed the 3 known findings.
- **P4.** I did not run it. The lead's P4 run, 7eaad48, used a tree whose reader, spelling, vocabulary, canonical, checker and `__main__` files are byte-identical to the frozen ones (READ the lead's log, MEASURED the hashes).

## Defects

**D1. Gate, a regression from cbdb6a3.**
- `python tools/check_privacy.py --control` exits 1 with `OSError: [WinError 6] The handle is invalid` when stdout is closed (`&gt;&amp;-`) or stderr is closed (`2&gt;&amp;-`). With stdout closed the traceback is in `subprocess._get_handles`. With stderr closed the exit is 1 and silent.
- cbdb6a3's gate exits 0 in every one of those cases (MEASURED, `check\g6_std.py`, a 64-row matrix of stdin × stdout × stderr × mode, old gate against new; direct repro in a clone).
- Run mode is unaffected, because all its git calls capture output.
- **Cause.** `control()` calls `git init -q` without capturing output. The new `git()` helper adds `stdin=DEVNULL` to that call. Python's Windows `subprocess` then has to duplicate the parent's stdout and stderr handles, and a closed one fails.
- CLAUDE.md item 8 recommends `&gt;&amp;-` for a closed stdout.
- No test catches it: the stdin test runs the gate with captured pipes for stdout and stderr.
- **Fix.** Adding `capture_output=True` to that one call made all 16 control-mode combinations exit 0, in a scratch copy (MEASURED, `check\g6_std_ctl.py`).

**D2. Gate, older than P0.7 but inside the O1 fix P0.7 took.**
- A clean sparse checkout now passes `privacy` but fails `privacy-controls`.
- **Reproduction.** In `git clone --sparse` of the committed tree with `sparse-checkout set --cone qro tools tests verify controls docs profile`, `bash verify/run.sh --only privacy,privacy-controls` gave privacy ok and privacy-controls FAIL, rc=1.
- **Where it fails.** After all 37 plants print "caught", `control` → `_copy` → `committed` raises `FileNotFoundError`. `_copy` still reads every tracked file from disk.
- **Wider reach.** Deleting any one tracked file from disk does the same: run mode exits 0, `--control` exits 1 with a traceback (MEASURED).
- At cbdb6a3 this was a clean "CONTROL REFUSED: the tree fails before any plant".
- The entry's "O1: a clean sparse checkout is no longer refused" is true of the run only. A fix would have `_copy` skip a tracked file that is absent from disk (BELIEVED, not tried).

**D3. Code and prose, the writer.**
- `canonical.write` still raises where the reader refuses. P0.7 fixed only the TypeError.
- **Reproduction.** `check\g3_min.py`: with `{"@type": "File"}` appended to the graph, `write` raises `KeyError '@id'`. The reader on the same metadata refuses `graph-form`, "an entity without @id or @type".
- **Other raising cases** (`check\g3_writer.py`):
  - an entity that is a string raises `ValueError`;
  - `@graph` a string raises `ValueError`;
  - `@graph` or `@context` missing raises `KeyError`;
  - an entity that is a list raises `KeyError`;
  - a reference dict with no `@id` inside a list term raises `KeyError`.
- The `write` docstring says metadata it cannot arrange is "refused as the reader refuses it, never a TypeError". The entry says it "now lets the reader refuse what it cannot arrange". Both are true of TypeError only.
- This answers scope item 3: no, it does not yet refuse everything the reader refuses.

**D4. Prose, FORMAT.md item 22's first rdflib bullet is false in part.**
- It says `@x`, `.`, `././`, `//` and `?` are the root at a directory base and the descriptor's IRI at the metadata file's own URL.
- At base `https://example.org/crate/ro-crate-metadata.json`, rdflib 7.6.0 reads `.` and `././` as `https://example.org/crate/`, the root. Only `@x`, `//` and `?` become the descriptor's IRI (MEASURED, a copy of P0.5's `claims4.py` under Python 3.13.5, sockets blocked).
- P0.5's note 4 named `@x`, `//`, `?` and `;`. The `;` sentence ("`;` the root") was not qualified. At that base `;` is the descriptor's IRI.

**D5. Prose, sentences left false or stale.**
- `qro/spelling.py:40` still says an absolute IRI is refused if its scheme is "a prefix of the context". The rule is now any term of the context.
- `qro/checker.py:19` says a reader or generator that fails on the crate's bytes "is refused by its step's name, never a crash".
- `CLAUDE.md:76-79` says a reader or generator that fails on a crate is refused by its step's name.
- Both of those lack the MemoryError exception that item 16 now carries.

## Notes below the bar

- **Test reach, the cap's number.** FORMAT.md and the entry say 4,096, but no test holds it. A mutant with `LINE_MAX = 9000` survived the whole suite. `LINE_MAX = 100` was killed, but only incidentally.
- **Test reach, the nets' width.** I widened both nets to `(MemoryError, RecursionError)`. That mutant survived all 2,923 tests, P1's 1,169 included. Only ZeroDivisionError is tested as still refused.
- **Test reach, the every-git test.** It wraps only `subprocess.run` and checks only stdin and creationflags, which is why D1 passed it.
- **Cut line.**
  - A cut line is 4,096 characters plus a notice, so about 4,125 bytes with the line feed.
  - A long `where` leaves no room for the detail.
  - In exit 2 and exit 3 lines the cut drops the trailer: "this is not a verdict", or the usage text.
  - The docstring's "reads back as the text's first characters" omits the appended notice.
- **O1 fail-open (BELIEVED, not demonstrated).** `os.path.lexists` returns False for a path Python cannot see. On Windows with LongPathsEnabled=0 and a tracked file whose on-disk path exceeds 260 characters, an unstaged edit to it is now skipped. Before P0.7 it was a finding. This machine has LongPathsEnabled=1, so I could not test it.
- **Item 16 wording.** "Whatever a step lets through is the checker failing, exit 3" omits PermissionError (exit 2), which the next bullet states.
- **Memory constant.** The path tree is linear but costs about 320 bytes a segment: 1,000,000 segments took 2.6 s and a 348 MB peak.

## What held

- **Reader tree.**
  - The new `_place` against cbdb6a3's inline logic gave identical refusals, texts included, over 93,195 exhaustive sequences and 300,000 random ones (`check\g1_place_diff.py`; also under Python 3.13.5).
  - On 40,000 hostile or near-valid whole-reader cases, 4,998 differed and every one carries a term-scheme id. None was refused before and accepted now, and neither reader raised anything but a refusal (`g7_*.py`).
  - Casefolding by segment equals casefolding the whole path: no code point folds to or from `/`.
  - **Timing.** Time is linear: a chain of 50,000 segments read in 0.118 s, and the old reader took 0.668 s at 10,000. Shapes tried were a chain, long segments, a wide directory, a comb, a fan, and case and kind clashes (`g1_perf.py`).
- **Id rule.**
  - The pinned context's digest matches. There are 3,069 terms plus `qro`, of which 334 have a scheme's shape.
  - 311 schemes are newly refused, exactly the shaped terms less the 23 prefixes, and no term-scheme id is accepted.
  - The six IANA-registered schemes, about, data and geo (permanent) and maps, query and tool (provisional), are correct. I checked them against the lead's downloaded copy of the registry, not a fresh fetch.
  - None of http, https, urn, doi, mailto, tag or ftp is a term.
  - No code string literal begins with a term scheme.
  - A one-byte change to the context file gives exit 3, as does a missing file.
- **rdflib claims** (MEASURED, 7.6.0):
  - The third-limit sentence is true: `mailto:`, `s3:` and `data:` bases give `.#a:b`, and an empty-path base gives `.#f`.
  - From a base's own path rdflib collapses `//`, removes dot segments and drops a final `;` for a fragment. It lowercases the base's scheme.
  - Told version 1.0, rdflib still reads 1.1's rule.
- **MemoryError.**
  - A process-level matrix of 12 exception types at 6 injection points (`g4_memerr.py`): MemoryError and a subclass give exit 3 from a reader, a generator, a count rule, a step, a file read and the reader's parse.
  - ZeroDivisionError and the other ordinary exceptions are still refused by name, with PermissionError exit 2 from count rules and steps.
- **The cut.**
  - Checked for every code point and offset at a small limit, and for 16 sample code points at the real cap; the escape is never split, the count is right, and `unicode_escape` reads it back.
  - A 50-million-character line is cut in 0.03 s.
  - P1.1's long-line reproductions now give 4,126-character lines (`g11_longline.py`).
- **Registry.** 25 plants in the lint line: options, `--`, `-`, duplicates, quoting, continuation lines and `&amp;&amp;` are all caught. A `need_env` before the lint stage passes every rule, as the docstring says.
- **Gate.**
  - Run mode exits 0 under every stdin state in the matrix.
  - Sparse checkouts (cone, cone plus sparse index, non-cone), a file deleted from disk, a file deleted and staged deleted, a skip-worktree index entry and an untracked keyed file: keys are found in each case and clean trees pass (`g6_sparse.py`).
  - `wsl-unc` newly finds exactly a slash after the host, and nothing benign (`g6_wsl.py`).
- **Mutants.**
  - The 23 distinct target ids of the lead's 29 mutants pass on the unmutated tree (356 passed), so those kills are real.
  - Of my 9 mutants, 5 were killed and 4 survived: `LINE_MAX = 9000`, the two widened nets, and `len &gt; 2`. The last is equivalent, because `cc` is the only 2-character scheme-shaped term and it is already a prefix.

## What I did not do

- I did not run P4's stages or read its worktree.
- I did not test CREATE_NO_WINDOW under pythonw, a detached process or a new console (host trap). I checked only that the flag is passed.
- I did not test LongPathsEnabled=0, Linux or macOS.
- I did not re-run the lead's 29 mutants, only baselined their targets.
- I did not run P1.1's memerr.py, which needs a memory cap on the shared host. The injection matrix stands in for it.
- I did not re-fetch IANA's registry.
- I did not run the suite under Python 3.13. I ran only my own scripts there.
