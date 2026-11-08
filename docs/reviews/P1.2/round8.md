**READY.** I found no defect in what the code does, and nothing blocks at this cap. I have four notes. Two of them (1 and 2) concern the seam.

## What I checked

All of this was run in my sandbox directory `p12-r8` through sbx.sh or sbx-mid.sh.

- **Freeze (MEASURED, `sha256sum -c`):** all 491 files of frozen\tree match SHA256SUMS, which begins `178a70bd`.
- **Whose files (MEASURED, diff against f0):** round 8 changed only P1.2's own files, P2's three, and the two new test files.
  - P2's three are `qro/p2_measures.py`, `docs/P2.md` and `tests/p2/test_p2_contract.py`.
  - The two new test files are `tests/p1/p1_standin.py` and `tests/p1/test_p1_merged.py`.
  - The P2 diff is only the ruled change: `question_files` returns `{}` for a crate with no source circuit, with its docstrings, the renamed contract test and limit 14. Nothing else of P2's moved.
  - The packet has no CRLF except five known `.out.txt` instrument outputs.
- **Runner, packet as a `git init` copy (5e39867):** passed 23, skipped 1 by name (p2-crates), failed 0. I ran it through sbx-mid.sh with both variables set.
- **Runner, packet laid on main af372ed (committed as 2e12f52):** passed 23, skipped 1 by name (p2-crates), failed 0. p1 passed 1,880 tests and p1-crates 42. P0.9's gate, ruff walk and refusal of names, and P4.2's changes, caused no failure of P1.2's.
- **Real crates (MEASURED, adapter as a process through sbx.sh):**

  | Crate | Files | Bytes | Identity | Checker |
  |---|---|---|---|---|
  | IBM | 1,074 | 53,443,198 | `88259c78…` | ACCEPTED |
  | Atlas | 32 | 5,076,857 | `f657f60e…` | ACCEPTED |

  - Built with P2 absent, the IBM crate has 1,072 files and 1,380 entities, and the Atlas crate has 30 files and 63 entities. Both are accepted.
  - The with-P2 counts are 1,595 entities for IBM and 116 for Atlas.
  - Every figure in docs/P1.md matches. The twin is 74 files with P2 and 73 without.
- **Seam, a crate P2 has no law for:** it is built with no `question/` files and none of P2's terms, accepted by the whole checker, and regenerates as built. A crate built with P2 absent and checked with P2 present is ACCEPTED. A crate built with P2 present and checked with P2's files truly absent is `REFUSED step-unbuilt`.
- **P2's raises (MEASURED):** I used a stand-in P2 that raises 15 classes in each of the two functions, run as a process.
  - ValueError, KeyError, RecursionError, UnicodeDecodeError, AssertionError and StopIteration each give exit 1 and one `REFUSED metadata-generated at qro.p2_measures: seam: &lt;function&gt; raised &lt;class&gt;` line.
  - OSError, FileNotFoundError, PermissionError, IsADirectoryError, MemoryError, KeyboardInterrupt, SystemExit, GeneratorExit and a bare BaseException each give exit 3.
  - Nothing is left in `--out` in any case.
- **The builder's reading on FileNotFoundError:** I judge it right.
  - In the adapter it is an OSError, so the host's failure and exit 3.
  - At check time a generator's OSError is refused by step 9's name, `metadata-generated`.
  - Only a hand-made crate with `question/` files but no `law.json` can reach it.
- **Hostile names from `question_files`:** the 13 I tried (`../`, `a/../b`, absolute, backslash, drive, `con`, `.`, empty, NUL, combining mark, trailing space, `:`, `law.json/`) each give exit 1 and write nothing. A good name builds.
- **Deep record (MEASURED):** at depths 500, 1,300, 1,500, 3,000 and 20,000 the adapter exits 1 with one REFUSED line and nothing left behind. The line is cut at `LINE_MAX` from about depth 1,500, with "(593 more characters)". The cut line still names the record. Past the reader's limit, the reader's own refusal appears.
- **Writes through a hard link:** I found none. The sandbox guard refuses such a write, and the runner passed under it. The helper `write_file` unlinks first.
- **Mutants of mine:** 9 beyond the builder's 19, run through sbx.sh against a clean baseline of 122 passed. All 9 were killed (6 by the targeted test and 3 by another test). They were:
  - the alone-twin pin removed;
  - the `new`-entities type check removed;
  - catching BaseException instead of Exception;
  - passing RecursionError through as the host's;
  - the Atlas path always calling `contribute`;
  - the case-fold check removed;
  - P2 reading the descriptor;
  - the tuple-length check removed;
  - the `question_files` dict check disabled.

## Defects

None, in code, gate or prose.

## Notes (these do not block)

1. **Prose, a limit the docs don't state, and a design consequence of the ruling.**
   - **What the checker accepts:** a crate that holds the very source circuit P2 knows, but was built with P2 absent, is accepted by the merged checker with no `question/law.json` and none of P2's terms. I built and checked this with the real records (identity `8ec4dc39…`). So the checker cannot tell "P2 had no law" from "P2's measures were stripped".
   - **Why:** whether the generator calls `contribute` depends on the crate's own `question/` files. Those files are what the crate holds, not what the records make.
   - **What the docs say:** the stated cost in docs/P1.md names only "another question, or a source circuit whose bytes moved".
   - **Fix:** the page should name this case. Alternatively, the generator could call `question_files` itself to decide.
2. **Contract gap, not code.** A P2 module that fails at import (I tried a raise and a SyntaxError) gives adapter exit 3, not the `seam` refusal. At check time it gives `metadata-generated`. The ruling names the functions only, and exit 3 is defensible for a broken install, but the docs do not say so.
3. **Behaviour that is unchanged:**
   - KeyboardInterrupt and SystemExit inside P2 give exit 3 "adapter itself failed". That was already so.
   - Pytest prints 376 `rm_rf` PytestWarnings. They come from other agents' `garbage-*` folders in the shared pytest temp folder, not from P1.2.
4. **Test reach is fine.** The seam tests use stand-in modules for both build and generation, and the real-P2 tests use one tree throughout. The pins' controls are killed by my mutants.

## What I did not do

- I did not exercise a real hard-link write in my own tests. I relied on the guard and the runner passing under it.
- I did not rerun the builder's 19 mutants.
- I did not read the lead's failed-run logs or crates.
- I did not run the p2-crates stage, which skips by name.

My notes are at `<scratch>\verifier-P12-r8\check\notes.md`.
