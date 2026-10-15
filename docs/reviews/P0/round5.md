The harness refused my write of `SCRATCH\verifier-P0-r5\report.md` ("Subagents should return findings as text"), so this message is the record. My scripts, logs and mutant lists are in `SCRATCH\verifier-P0-r5\check\` (mutation work in `check\mut\`). Nothing in `frozen\` or in the real repository was edited. Claims are labelled READ (in a file), MEASURED (I ran it, with the command or script named) or BELIEVED (my inference).

# P0 verifier, round 5: scoped re-check

## 1. Verdict: NOT READY

There are five defects. None is a wrong accept in the shipped code. Three fuzz runs found no disagreement, no crash and no second spelling (MEASURED, `fuzz_sweep.py`, `fuzz_reader.py`, `fuzz_custody.py`):
- 1,850,281 strings against the sweep's own statements;
- 121,950 mutants of the twin's metadata;
- 120,000 mutants of a custody log and record.

As in rounds 3 and 4, each defect is a sentence that claims more than the code or the test holds, or a plant that a second cause of refusal masks.

- **R5-1.** `tests/format/test_sweep.py` says it holds each spelling "over every one-character change to their examples". It tries 107 characters. Faults at 57 of 71 sites of the text spelling's deny list leave all 707 tests green, and one is shown accepting a control character.
- **R5-2.** `tests/docs/test_docs.py:66-68` still says item 8 "counts nothing". The code looks before the item's first colon only. R4-3(a) fixed FORMAT.md and the ledger but not this sentence.
- **R5-3.** "A path the host will not look at is misuse: exit 2" holds for a `stat` that raises. For a log, a record, the metadata file, a listed file or the crate directory that the user may not read or search, the command line exits 3, "the checker itself failed".
- **R5-4.** `docs/reviews/P0/README.md:3` says "Collected 2026-10-14". `round4.md` was collected on 2026-10-15.
- **R5-5.** Two plants are refused for a second reason. The "unequal-bitstrings" case has no final line feed. The fixture crate, which holds a raw result, masks a fixture generator registered without `--fixtures`.

What holds up, against my own plants:
- the freeze, at the start and the end: 239 files, 0 not OK, no extra file, no `.pyc`;
- the runner: 17 of 17 in a `git init` copy, 14 of 14 quick, and 17 of 17 in a committed clone that stayed clean;
- a commit of all 239 files with the harness's attribution line, cloned under both `core.autocrlf` settings: 0 files differ from SHA256SUMS, and the privacy gate accepts the `Co-Authored-By: ... <noreply@anthropic.com>` line;
- R4-1's five faults, R4-2's real gaps (the device digits, the time's separators, the atoms, the scheme's first class, the walk two levels down), R4-3(b), R4-4 and R4-5;
- every figure in the lead's measured block, reproduced (4.2);
- all 17 review copies against their sources, and `round4.md` against its verifier's final message.

## 2. Setup

- **Freeze.** MEASURED: `cd frozen/tree && sha256sum -c ../SHA256SUMS.txt` gives 239 OK and no other line, and the file lists are equal, at the start and at the end.
- **Hosts.**
  - Windows 11, Git Bash, Python 3.12.9, git 2.45.2.
  - WSL2 Ubuntu 22.04 (`cft2204`), Python 3.10.12, ext4 and not `/mnt/c`. I also ran there as `nobody`.
  - Every probe that shelled out named Git Bash by its full path.
- **Runner.**
  - MEASURED: `QRO_MOTH_ROOT=<repos>/moth-quantum bash verify/run.sh` in a `git init` copy (moth-quantum at 3a73823, read only). Run `20261015-023232-39715-nocommit+dirty`: passed 17, failed 0, skipped 0, 74 s wall (`check\run_full_clean.log`).
  - The stage counts equal the ledger's last block: docs 63, tool-tests 39, vocab-tests 7, format 564, custody 19, control-tests 15, controls-run 9 of 9 with 21 pending, study-plants 68 faults refused and 6 right variants accepted, privacy 239 files with none binary, privacy-controls 33 of 33, instruments 5 of 5, check-docs 10 documents with 22 other markdown files and 34 source files, the twin `ff3fe486…`, and the negative control refused `raw-digest at data/raw.counts.json`.
- **Quick and skip.** MEASURED: `--budget quick` passed 14 of 14 in 25 s wall (23 s of stage time). Without `QRO_MOTH_ROOT`, `instruments` skips by name and the run ends "PASSED, with 1 skipped by name above". With `--require-all` it fails.
- **Commit trial.**
  - MEASURED (`check\clone_trial5.sh`, `RUN=1`): 239 files committed in a scratch repository, cloned with `core.autocrlf` true and false.
  - In each clone 0 files differ from SHA256SUMS. The privacy gate reads 239 files and 1 commit message and finds nothing. `git status` is clean.
  - The whole runner in the `false` clone: run `20261015-033402-52258-e89b55b`, 17 of 17, and 0 `git status` entries after it.
- **Linux.**
  - MEASURED (WSL2): `tests/format`, `custody`, `controls`, `vocabulary` and `tools` give 644 passed, and `tests/docs` gives 63.
  - Windows gives 707 across the six directories (564 + 19 + 15 + 7 + 39 + 63). Four `PYTHONHASHSEED` values (0, 1, 7, 4242) give 707 passed each. No test skipped.

## 3. Defects

### R5-1. The sweep holds less than the sentence over it

- **Where.**
  - `tests/format/test_sweep.py:1-9`: "Each spelling, the path rule, the @id rule and absolute(), held to an independent statement of its rule over every one-character change to their examples".
  - `:27`: `ODD`, twelve characters: TAB, LF, CR, NUL, DEL, U+0085, U+00A0, U+00E9, U+0662, U+FF12, U+2028, U+D800. With the 95 printable ones, the alphabet is 107.
  - `docs/VALIDATION.md:593`, the R4-2 row: "holds each spelling ... to an independent statement". The row does state the alphabet; the docstring does not.
  - `qro/spelling.py:38`: `_TEXT_BAD`, a deny list of 64 control characters and the surrogates. Round 4's class-member removal skipped it as a deny list.
- **MEASURED.** `check\mut\tools\mutants\m_text.py` through round 4's harness (`hm2.py`): one mutant per control character removed from `_TEXT_BAD`, and seven surrogate edits. Of 71, 14 are killed and **57 survive**.
  - Survivors: 53 of the 64 controls (U+0001 to U+0008, U+000E to U+001A, U+001C to U+001E, U+0081 to U+0084, U+0086 to U+009E), and 4 surrogate edits (U+DFFF, U+D83D, U+DC00, and the whole low-surrogate range).
  - The killed ones are exactly the characters some test names: U+0000, 0009, 000B, 000C, 000D, 001B, 001F, 007F, 0080, 0085, 009F, and the edits that touch U+D800.
  - A string one insertion from the example `a name`, with U+0001 in it, is "within one change", is refused by the statement, and is never tried.
- **A fault that shows it** (`check\demo_text.py`). One edit to a copy of `qro/spelling.py`: U+0001 leaves `_TEXT_BAD`. The suite stays green (mutant 1 of `m_text`, through the whole pytest run and every extra stage). A twin whose header term `qro:writer` holds U+0001:
  - shipped: exit 1, `REFUSED spelling at ./ qro:writer: a control character other than a line feed, or a lone surrogate`;
  - edited: exit 0, `ACCEPTED ff3fe486…`, the twin's own identity.
- **The same docstring says more in two other places.**
  - "Each spelling": `integer`, `ref`, `slot` and the word sets are not in `RULES`, and the table is not read. A string spelling added to `SPELLINGS` joins the sweep only if someone adds it.
  - "Independent": the `binary64` statement calls `S.exact_decimal`, and the `text` statement calls `str.strip`, as the code does. The prose does not say which spaces "no space at either end" means.
- **Fix.** Add every C0 and C1 control, DEL, a lone low surrogate and one astral character to `ODD`, so that the 53 die. Or restate the docstring as "within one change, over these 107 characters", and name the spellings it sweeps.

### R5-2. Item 8's test still says it counts nothing

- **READ.**
  - `tests/docs/test_docs.py:66-68`: the function "names no refusal the table lacks, and counts nothing".
  - `:77-79`: `lead = item.split(":", 1)[0]`, and the number words and digits are looked for in `lead` only.
  - FORMAT.md item 8 now says "no count of them before this colon", which is exact. The ledger's R4-3 row says the same. The docstring was left.
- **MEASURED** (round 4's `probe_item8.py`, on the new tree). A count in the lead sentence is caught. These are not, each returning an empty list: "(the fourth name)", "the eighth of eight", "(8 in all)", "Eight names in all." on its own line, "about a dozen names here".
- **Why it matters.** This is R4-3(a) one sentence further on. The instance is fixed, and the class (a sentence over a test that claims more than the test holds) is not.
- **Fix.** Say "before the first colon" in the docstring.

### R5-3. "A path the host will not look at is misuse: exit 2" holds for a `stat` that raises, not for a read or a search

- **READ.**
  - `qro/__main__.py:8-9`: "or a path the host will not look at, is misuse: 2".
  - `docs/FORMAT.md:135-137`: "or a path the host will not look at, is misuse: exit 2".
  - `docs/VALIDATION.md:604`: "A path the host will not look at, a 300-character name say, is misuse: exit 2, not 3."
  - `kind()` (`__main__.py:45-50`) wraps `Path.is_dir` and `Path.is_file` only. The reads at `:88` and `:91`, and everything the checker opens, are not wrapped.
- **MEASURED** (WSL2 ext4, run as `nobody` so that mode bits bind; `check\probe_perm.sh` and `probe_perm2.sh`):

| the path | the command | exit and line |
|---|---|---|
| a custody log, mode 000 | `custody LOG` | 3, `FAILED: the checker itself failed, PermissionError: ... Permission denied` |
| an audit record, mode 000 | `custody LOG REC` | 3, the same |
| the crate's metadata file, mode 000 | `check CRATE` | 3, the same |
| a listed file, mode 000 | `check CRATE` | 3, the same |
| the crate directory, mode 000 or 444 | `check CRATE` | 3, the same |
| a parent the user cannot search | `check PATH` | 2, as claimed |
| a 300-character name | `check PATH` | 2, as claimed |

- **Why it is a defect.** "The checker itself failed" is exit 3's meaning, and a user's own permissions are not the checker failing. The test's docstring defines "look at" as the `stat` that raises (`test_cli.py:345-349`). FORMAT.md and the command line's docstring do not.
- **Fix.** Catch `OSError` around the reads and the crate's first look, and answer 2 with "cannot read". Or write "a path the host will not report on" in the three places.

### R5-4. The reviews README dates round 4's report a day early

- **READ.** `docs/reviews/P0/README.md:3`: "Each report as its verifier returned it. Collected 2026-10-14." The ledger heads the round-4 entry `2026-10-15`.
- **MEASURED.** The round-4 verifier's transcript runs from 2026-10-15T07:44Z to 2026-10-15T08:49Z (00:44 to 01:49 local). `round4.md` is its last message, and its source file was staged at 01:51 on the 15th. The placing script (`SCRATCH\reviews\place_reviews_r4.py`) writes the date as a constant.
- **Fix.** "Collected 2026-10-14, and round 4's on 2026-10-15", or a date a row.

### R5-5. Two plants are masked by a second cause of refusal

- **(a) "unequal-bitstrings".**
  - READ: `tests/format/test_hostile.py:98-99` plants `b'{"00":1,"011":2}'` with no final line feed. The fixture's raw-form reader (`qro/fixture.py:36-39`) refuses it as "not its one canonical line" before it reaches the width rule (`:41-43`).
  - MEASURED: `read_counts(b'{"00":1,"011":2}')` gives "not its one canonical line". With the line feed it gives "'011' is not a bitstring of the first one's length".
  - Faults that leave the suite green (my operator E, `mut\tools\ast_gen_e.py`, mutants 513, 514, 520, 521): the width and alphabet `raise` removed; `re.fullmatch` made `re.match` or `re.search`, so that the key `01x` is read; the non-negative-count `raise` removed.
- **(b) The twin masks half a registration.**
  - READ: `tests/format/test_cli.py:242-249`, R4-1's first fix, plants the twin without `--fixtures`. The twin holds a raw result, so a missing raw-form reader refuses it whatever the generator.
  - MEASURED (`check\demo_register.py`, `m_reg.py` mutant 2): one line in a copy of `qro/fixture.py` registers `GENERATOR` at import. The suite stays green. A crate of the fixture's notes file alone, whose metadata the fixture's generator wrote and which names it:
    - shipped, `check CRATE` without `--fixtures`: exit 1, `REFUSED step-unbuilt at ./ qro:generator: no generator qro-fixture is built`;
    - edited: exit 0, `ACCEPTED f51b59c5…`.
  - This is R4-1's row 1 in a form its test does not see. Registering the raw form alone at import (mutant 1) is equivalent in verdict, since step 9 still refuses.
- **Fix.** (a) Add the line feed, and cases for a non-bit key, `01x` and a negative count. (b) Plant a crate with no raw result, and assert both registries are empty after a run without the flag.

## 4. Per scope item

### 4.1 R4-1 to R4-5

| item | verdict | evidence |
|---|---|---|
| R4-1, the command line | the five faults are killed; two variants are not (R5-5b, R5-3) | MEASURED: round 4's `m_cli4`: 10 killed, 1 survivor, 5 not applicable (their text changed). The lead's `m_cli_r4` (5 rewritten, 3 added): 8 of 8 killed. The lead's `m_cli`: 16 killed, 2 not applicable. My `m_new` (45 mutants at the command line, `kind()`, `absolute()` and `IRI`): 36 killed, 9 survive, listed in 4.2. Process runs on Windows through Git Bash (`probe_cli5.py`): a pipe, `>&-`, `>&- 2>&-`, `\| head -c 0`, `\| true`, misuse with stderr closed, the module not importable, a trailing slash, a non-ASCII crate path in three console encodings. All agree with the docstring. |
| R4-2, the refused side | the pattern-level gaps are closed; the deny list is not (R5-1) | MEASURED: every gap round 4 named is killed: `m_x4b` 324 of 332, `m_x7` 72 of 74, `m_x8` 69 of 75, and the walk two levels down in `m_rows`. |
| R4-3(a), item 8's count | FORMAT.md and the ledger exact; the docstring is not (R5-2) | |
| R4-3(b), `MUST_SAY` | holds | MEASURED (`probe_registry.py`, `probe_shape.py`). Caught: `""`, `"R"`, `"REFUSED"`, `"REFUSED file-digest"`, and my variants (a space either side, single quotes, lower case, a plant that does not exist, `MUST_FAIL=0`, `MUST_FAIL` absent, a plant whose row expects `accepted`, `float-spelt` with `raw-digest` said). Not caught: a second negative control with an empty `MUST_SAY`, since `re.search` takes the first. |
| R4-4, the headers | holds, with one nit | MEASURED (`diff` against `git show 3a73823:` of each file, read only): `check_docs.py`'s header names both dropped sentences and everything else in the diff but one clause (note 7). `run.sh`'s header is exact. `pytest-stage.sh` differs by its two header lines, as it says. |
| R4-5, `graph-form` | holds | MEASURED: 15 `Refused("graph-form", ...)` sites (`reader.py` 122, 128, 142, 162, 167, 169, 171, 175, 178, 181, 184, 188, 194, 212; `checker.py` 112). The row names each, the root's `conformsTo` and the two-entity minimum included. |

### 4.2 The mutation tests

I ran every set against the six directories the runner runs (707 tests). A survivor then ran against the twin, the negative control, `gen_vocabulary --check`, `controls.run`, `check_docs` and ruff. The harness counts a pytest failure or a 300 s timeout as a kill. D, `m_cli4`, `m_rows`, `m_x4b`, `m_x7` and `m_x8` are round 4's operator and sets. I regenerated `m_x4b` against the new source with `IRI` named, and ran the old `m_x4` as it was, from round 3's old source.

| set | mutants | killed | survived | not applicable | survivors |
|---|---|---|---|---|---|
| D (`ast_gen.py`, `hmp.py`) over reader, checker, custody, spelling, canonical, `__main__` | 452 | 441 | 11 | 0 | 11 equivalent |
| round 3's command-line set (`m_x3`) | 37 | 9 | 1 | 27 | 1 equivalent |
| the lead's `m_cli` | 18 | 16 | 0 | 2 | |
| the lead's `m_cli_r4` | 8 | 8 | 0 | 0 | |
| round 4's `m_cli4` | 16 | 10 | 1 | 5 | 1 equivalent |
| path alphabet (`m_x1`, `m_x5`) | 99 | 97 | 1 | 1 | 1 equivalent |
| path and reader variants (`m_x2`) | 39 | 36 | 3 | 0 | 3 equivalent |
| class-member removal from round 3's old source (`m_x4`) | 372 | 232 | 8 | 132 | 8 equivalent |
| the lead's scheme and IRI-tail removal | 210 | 210 | 0 | 0 | |
| class-member removal, adapted, `IRI` named (`m_x4b`) | 332 | 324 | 8 | 0 | 8 equivalent |
| `_ID` and the IRI tail, every member of `[!-~]` (`m_x6b`) | 188 | 188 | 0 | 0 | |
| round 3's 15 rows and 25 variants (`m_rows`) | 42 | 40 | 2 | 0 | 2 equivalent |
| quantifiers, separators, branches (`m_x7`) | 74 | 72 | 2 | 0 | 2 equivalent |
| each atom a wildcard (`m_x8`) | 75 | 69 | 6 | 0 | 6 equivalent |
| round 2's list (`m_r2`) | 68 | 49 | 4 | 15 | 4 equivalent |
| the lead's earlier list (`m_lead`) | 29 | 22 | 0 | 7 | |
| **mine:** `[0-9]` widened to `\d` with `re.ASCII` dropped, place by place (`m_digit`) | 17 | 14 | 3 | 0 | 3 equivalent on CPython |
| **mine:** `kind()`, `absolute()`, `IRI`, `escape`, `write` (`m_new`) | 45 | 36 | 9 | 0 | 7 equivalent, 2 gaps |
| **mine:** `_TEXT_BAD`, member by member (`m_text`) | 71 | 14 | 57 | 0 | 57 gaps (R5-1) |
| **mine:** registration at import (`m_reg`) | 5 | 3 | 2 | 0 | 1 equivalent, 1 gap (R5-5b) |
| **mine:** operator E over `qro/` (`ast_gen_e.py`) | 525 | 466 | 58 | 1 | 45 equivalent, 13 gaps |

I did not re-run the 94 `_BINARY64` members of round 4's `m_x6`. Round 4 argued all 94 equivalent, and 13 are in `m_x4b`, with 8 surviving.

**The lead's measured block against my runs.** Every figure reproduces:
- the command-line set: 10 killed, 1 survivor, 5 not applicable; the 8 rewritten or added: 8 of 8;
- round 4's rows: 42, with 40 killed and the two equivalents named;
- class-member removal:
  - Round 4's `m_x4b` has exactly 13 mutants whose text moved, every one an `_IRI` tail member (`applicable.py`). So 332 gives 311 killed, 8 survivors and 13 not applicable.
  - My version with `IRI` named kills those 13 as well: 324 and 8. The lead's 210 of 210 reproduces;
- quantifiers: 74, 72 killed; atoms: 75, 69 killed, the 6 survivors being one `_BINARY64` wildcard and five `_DATE` wildcards.

**D's eleven survivors, with the argument.** They are round 4's list at new line numbers.
- `reader.py:40`, `seen.add(k)` deleted: a repeated key fails the re-serialisation with the same name, `spelling`.
- `reader.py:127`, `2` to `1`: a one-entity graph is refused `graph-form` at `@graph` later.
- `spelling.py:47`, `>> 62`: the test is on truthiness, and the two zeros give 0 and 2.
- `spelling.py:49`, three: the branch sees only infinities.
- `spelling.py:95`, a size of 20 digits: any 20-digit decimal exceeds 2^63 - 1 and fails the next test.
- `__main__.py:35`, two: space and `~` pass through `unicode_escape` unchanged.
- `__main__.py:63`, `3` to `4` or `2`: the second write goes to the descriptor that has just failed.

One further D mutant, `spelling.py:68`, is killed by lint only, as in round 4.

**The date wildcards and the `\d` survivors are equivalent on CPython** (BELIEVED, with evidence).
- MEASURED (`witness_date.py`): 133,350 strings for each of the five wildcards, and none is one the wildcard admits and `date.fromisoformat` accepts.
- MEASURED: `date.fromisoformat` refuses Arabic-Indic and fullwidth digits. So the `_DATE` pattern's `re.ASCII` is redundant here. A pure-Python `datetime` would differ.

**Operator E's 13 gaps.** The other 45 survivors are equivalent: a verdict of the same name by another check, a message only, an ASCII `lower()` for `casefold()`, or a `set` for a list. None of the 13 is claimed held by a tree sentence, except the fixture's, which is R5-5a.
- `reader.py:149`, `t != sorted(set(t))` to `sorted(t)`: **a type listed twice is accepted.** MEASURED (`demo_type.py`): edited, `reader.read` accepts `"@type": ["File", "File"]`. Shipped refuses it `spelling`.
- `spelling.py:105`, `n.lstrip("-")` dropped: a negative numerator of 1,000 digits would be refused. The shipped code accepts it; the tests hold only the 1,001-digit refusal.
- `checker.py:66` (4 mutants) and `:101` (2): the walk's `sorted()` calls. MEASURED (`demo_order.py`): with `sorted(on_disk)` removed, a crate of five unlisted files is refused at five different files over twelve hash seeds. The shipped code names `data/stray-a.txt` every time. Lines 82 and 98 are equivalent, since the reader fixes the graph's order.
- `fixture.py:42-45` (4): R5-5a.
- `reader.py:53`, the `RuntimeError` when the RO-Crate context is not the pinned copy. No test tampers with the file. `qro/data/README.md:8-9` says "the strict reader refuses to load any other bytes". It does: MEASURED, one space appended to a copy exits 3 with "not the copy the vocabulary pins". Nothing holds it.

**My `m_new` survivors.**
- Equivalent: `IRI` and `SCHEME` without `re.ASCII`; `escape` with the space, `~` or `"` sent through `unicode_escape`; the custody message naming the last missing path; `os.walk(followlinks=True)`, since the walk refuses a link before it recurses.
- Gaps:
  - `kind()` narrowed to `PermissionError` survives on Windows. It is killed on Linux, where a 300-character name raises `OSError` (MEASURED on WSL).
  - The crate test replaced by "has a metadata file" survives, so no test runs the command line on an empty directory. Shipped: exit 1, `file-missing`. Edited: exit 2.

### 4.3 The sweep, `tests/format/test_sweep.py`

Is each statement a faithful reading of its rule's prose? Yes, with three exceptions (READ, against `qro/vocabulary.py`'s `SPELLINGS`, FORMAT.md item 11 and the code):
- **`iri`.** The statement requires something after the `:`. FORMAT.md item 11 and `absolute()`'s docstring say so. `SPELLINGS`' `iri` text, and so the generated VOCABULARY.md, says only "a scheme of two characters or more with no dot, then ':'". MEASURED: `problem("iri", "http:")` refuses it.
- **`text`.** "No space at either end" is read as `str.strip()`, as the code does. U+00A0, U+2028 and U+3000 at an end are refused. The prose does not say.
- **`binary64`.** The decimal is compared with `S.exact_decimal`, the function under test. The explicit check is the nine values of `test_exact_decimal_is_cft_fp256s_spelling`.

The rest (`size`, `digest`, `commit`, `rational`, `time`, `date`, `id`, `path`, `absolute`) read the prose and not the patterns. `path` reads FORMAT.md item 11 to the letter: the character set, the empty segment, 255, `.` and `..`, the trailing dot, and the 26 device names with or without an extension.

Does the docstring claim only what the test holds? No: R5-1. "Within one change" is true of the strings, and the alphabet is not stated. "What this holds, and no more" is the honest sentence; the first paragraph does not match it.

### 4.4 Round 4's notes 1 to 10

| note | as the ledger says? | evidence and where it is stated |
|---|---|---|
| 1, a stage the shell never reaches | taken; holds | MEASURED (`probe_registry.py` on the new tree): `if false`, a here-doc comment, an `exit 0` before a stage and a `need` that always skips are unseen. Stated in `test_stage_registry.py:24-27`; not in CLAUDE.md, whose sentence is unqualified. |
| 2, a tool's own mask | taken; holds | `--help` and `--exit-zero` unseen. Same docstring. |
| 3, the runner's exit | taken; holds | The removed `exit 1` is unseen. A `stage()` that ignores `rc` is unseen by the registry, and the negative control fails the run (round 4's note). Same docstring. |
| 4, a partial line under exit 3 | taken; holds | READ: FORMAT.md item 16, `__main__.py:18`. Planted at `test_cli.py:283-296`. |
| 5, a path the host will not look at | taken; holds for `stat` only | R5-3. |
| 6, `absolute("http:")` | taken; holds | MEASURED: `absolute("http:")` false and `problem("iri", "http:")` refused. FORMAT.md item 11 and the docstring say so. |
| 7, start failure exits 1 | taken; holds | READ: FORMAT.md item 16, CLAUDE.md:51-56, `__main__.py:20-21`. MEASURED: with no `qro` on the path, exit 1, "No module named qro", nothing on stdout. |
| 8, REFUSALS.md's other rows | not taken; as the ledger says | The ledger alone says the rows are summaries. REFUSALS.md and `vocabulary.py` do not, and only `graph-form` reads as a list. |
| 9, a non-ASCII digit at every place | taken; holds for the time | MEASURED: `m_digit` kills the widening at all eight classes of `_TIME`, and in `_DECIMAL` and `_RATIONAL`. The date's three survive and are equivalent on CPython. |
| 10, an exit or an interrupt | taken; holds | MEASURED: `SystemExit(0)`, `SystemExit(1)`, `KeyboardInterrupt` and `MemoryError` each exit 3 and are planted. Narrowing the catch is killed. |

### 4.5 The changes beyond round 4's findings

- **`absolute()` is the `iri` spelling.**
  - It holds: one pattern, `IRI`. The lead's 210 mutants and my `m_new` set on it are killed.
  - It wrongly refuses nothing legitimate. A one-letter or dotted scheme, and an empty tail, are refused by design, and said.
  - One effect is unstated. MEASURED (`probe_absolute.py`, round 4's tree against this one): a reference whose IRI-shaped id holds a space, a control character, a tab or a non-ASCII character was refused `spelling`. It is now refused `graph-form`, with the detail "... names no entity in the graph". The same holds for `http:`, `https:` and `ab:`, which round 4's reader let through step 1. Nothing pins either name, and the reader's docstring ("every reference to a relative @id naming an entity") does not cover an IRI.
- **The command line catches `BaseException`.** It holds. `SystemExit(0)`, `SystemExit(1)`, `KeyboardInterrupt`, `MemoryError` and an ordinary crash each exit 3 with one `FAILED` line. Narrowing the catch to `Exception`, or to common errors, is killed. An interrupt during the write itself is not inside the checker, and is not claimed.
- **A path the host will not look at.** R5-3.

### 4.6 Anything else in the tree that is now false

- R5-1 to R5-5.
- **CLAUDE.md:9**, "~15 s" for `--budget quick`: 25 s wall here, 22 s in round 4. The full run's "~75 s" holds (74 s).
- **FORMAT.md item 12**, "A symbolic link or a junction anywhere in it is refused `file-link`": see note 1.
- **`qro/spelling.py:72-79`**, `time()` is "the one spelling of an aware datetime". MEASURED on WSL (glibc): `S.time(datetime(5, 1, 2, 3, 4, 5, tzinfo=utc))` is `'5-01-02T03:04:05Z'`, which the reader refuses. On Windows it is `'0005-…'`. No production code calls it.
- CLAUDE.md, README.md, NOTICE.md and `docs/README.md` otherwise agree with the code and the files. MEASURED against the records:
  - 65 job files and 7 snapshots;
  - the omitted keys (`user_id`, `cost`, `estimated_running_time_seconds`, `circuits_execution_time_ns`) appear only as values of the `*_omitted_keys` lists;
  - the usage's metric id is one value in all 65;
  - exactly 5 instrument outputs and 3 logs hold CRLF;
  - NOTICE.md's citations equal the terms report's table.

### 4.7 The review copies

- **Copy against source.** MEASURED (`check\review_check5.py`, my line-level check, run on all 17 copies; `review_ph5.py`; `review_angle5.py`).
  - Every study copy equals its source after the stated changes, with 0 unexplained lines.
  - Per file, the README's columns equal what I measured: the CRLF counts (291, 395, 226, 202, 270, 172, 131), wrapper yes or no, final line feed, home-path counts (1, 1, 0, 0, 1, 1, 0, 1, 1, 0, 0, 1), and all twelve SHA-256 prefixes.
  - The seven wrapped sources carry the nine tags the README lists. No report body holds a raw `<` or `>`.
  - The P0 copies: `round1-interim.md` has 4 `<a home path>` where its source has none, `round1.md` has 1, `round2.md` has 1 `<repos>`, and `round3.md` and `round4.md` equal their sources byte for byte (`round4.md` SHA-256 `80690752…`). The lead's counts equal the README's.
  - My line-level test left one line of `round1-interim.md` unexplained, as in round 4. The four redacted spans are UNC and drive-letter shapes that my loose test does not recognise (`review_debug5.py`).
- **Source against verifier.** MEASURED (`sources_vs_transcripts5.py`, `tx_last.py`; counts and booleans only).
  - 11 of the 12 study sources equal the last long message of a subagent transcript, and the task id in each wrapper names it. The twelfth, draft 4's, is the lead's transcription.
  - `round4.md` equals the last assistant record of the round-4 verifier's transcript: stop reason `end_turn`, one text block of 34,539 characters, equal to the staged source after stripping and one line feed. The placed copy equals it. Its first prompt names round 4 and R3-1.
- **The one error** is R5-4.

## 5. Notes (below the bar of a defect)

1. **The walk is blind to a directory it cannot list, and says nothing.**
   - MEASURED (`probe_perm.sh`, cases 5 and 15; `os.walk` is called without `onerror`): a crate with `hidden/stray.txt` and a symbolic link out of the crate inside a mode-000 `hidden/`, checked as a user who cannot list it, gives `ACCEPTED ff3fe486…`, the twin's identity.
   - With the directory readable: `REFUSED file-unlisted at hidden/stray.txt`, or `file-link` for the link.
   - FORMAT.md's "What the walk cannot see is not checked" covers it in general, and its three examples do not name it. BELIEVED: raising on a directory the walk cannot list is one argument for fixing it.
2. **The two closed-descriptor tests depend on `PATH`.** `test_cli.py:334` uses `shutil.which("bash")`, and the docstring says "the runner's own bash". MEASURED: from PowerShell, `which` finds `C:\Windows\system32\bash.EXE` (WSL's), and both cases fail with `rc=0`. They pass under the runner. CLAUDE.md says to use the runner.
3. **The `iri` prose** (`vocabulary.py`, VOCABULARY.md) does not say a tail must follow the `:`.
4. **`absolute()`'s effect on a malformed IRI reference** (4.5) is unstated.
5. **Checks held by no test** (4.2): a type listed twice; a negative 1,000-digit numerator; the walk's `sorted()` at `checker.py:66` and `:101`; the RO-Crate context's pin; the command line on an empty directory; `kind()` narrower than `OSError` on Windows.
6. **CLAUDE.md's "~15 s"** (4.6).
7. **`check_docs.py`'s header** says "the summary counts the source files". The summary also counts "other markdown files" and adds "and every path named exists". Same kind as R4-4, one clause each.
8. **The registry** sees only the first negative control. A second with an empty `MUST_SAY` passes `shape_problems`. There is one.
9. **`tests/format/test_sites.py:118` leaks a temp directory each run** (`tempfile.mkdtemp()`, never removed). My runs left 1,457 under the system temp; the list is `check\leaked_tmp_dirs.txt`. 2,503 more of the same shape predate my session. I removed none.
10. **`check ""`** checks the current directory as a crate (`Path("")` is `.`). A symbolic link to a crate, and a link to a log, are followed and accepted.
11. **`README:hidden`** still reads as an IRI. The stated limit is unchanged and still true.
12. **On this Windows 11 build (22631), `open()` in a scratch subdirectory created `CON`, `PRN`, `AUX`, `COM0` to `COM10` and `LPT0` to `LPT9` as ordinary files** (MEASURED). Only `NUL` and `nul.` behaved as devices. The path rule is a superset here, as FORMAT.md says. Windows' documentation still lists the names.

## 6. What I did not do

- **No macOS, no real Windows console, no Windows ACL change.** The permission cases ran on WSL2 as `nobody`. Linux is Python 3.10.12, not 3.12.
- **No mutation of `controls/`, `tools/` or the tests**, and I did not re-run `m_x6`'s 94 `_BINARY64` members.
- **No IBM or Atlas contact; no qiskit; nothing submitted.**
  - I did not open `~/.quantum-film`, any `.atlas` directory, or any key, token or CRN.
  - I read the subagents' transcripts under `~/.claude` only to compare messages, and printed counts and booleans from them.
  - No job id is in this report: I printed none, and counted them only. Every key-shaped string in my scripts is made up.
- **I did not re-read IBM's or Moth's terms.** I checked NOTICE.md's citations against the terms report's table, and its record statements against the records.
- **No `rocrate-validator`, no JSON-LD processor, no review of P1 to P5.**
- **Files I wrote outside `check\`:** two scratch copies of the tree in WSL's `/tmp/r5` (removed), three file-name lists in Git Bash's `/tmp` (removed), and pytest's own temp directories (note 9).
- **Slips of mine.**
  - My first background run of the runner used an inner `&`, and a second run's `rm -rf .gate-state` deleted its state directory, so that log is garbled. I re-ran in a fresh copy; `run_full_clean.log` is the record.
  - Writing `m_text.py` through the file tool merged `\udbff\udc01` into one astral character, so the U+DC00 mutant was killed for the wrong reason. I rebuilt it from `chr(92)` pieces and re-ran it: it survives. The table above is the corrected count, 57 survivors and not 56.
  - My first fuzz of the reader counted every accepted mutant that was not the original bytes as a fault, and most were valid crates with another value. I re-ran it counting the same parsed value in other bytes: 0.
  - A first `probe_cli5` crate path was relative to the wrong directory.
- **No one was contacted, and no banner accepted.**

A scoped re-check after the fixes should re-run `m_text` (with `ODD` widened), `m_reg`, operator E's `fixture.py` and `reader.py:149` mutants, and the probes `probe_item8.py`, `probe_perm.sh` and `probe_perm2.sh`. I will pick my own faults again.
