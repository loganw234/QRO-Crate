The harness refused my write of `SCRATCH\verifier-P0-r4\report.md` ("Subagents should return findings as text"), so this message is the record. My scripts, logs and mutant lists are in `SCRATCH\verifier-P0-r4\check\`. Nothing in `frozen\` or in the real repository was edited. Claims are labelled READ (in a file), MEASURED (I ran it) or BELIEVED (my inference).

# P0 verifier, round 4: scoped re-check

## 1. Verdict: NOT READY

There are five defects. None is a wrong accept in the shipped code: in every run of mine it gave the right answer. As in round 3, each defect is a check that the suite lets a fault through, or a sentence that claims more than the code or the test does.

- **R4-1.** The command line's fix (R3-1) holds in every case I ran as a process. Its tests leave four faults green: the fixture registered without `--fixtures`, a path of the wrong kind, a partial write, and both descriptors failing.
- **R4-2.** R3-2's class is still open in the spellings, the path rule and the walk. Faults at 68 sites leave all 660 tests green. Among them: `COM3` and `LPT7` accepted into a crate, and a header time with `x` for both colons accepted.
- **R4-3.** R3-3's class again. Two tests hold less than the sentence over them: FORMAT.md's "no count of them" (item 8) and the registry's "the negative control names the refusal it must fail with".
- **R4-4.** R3-4's class again. The header of `tools/check_docs.py` still lists one change too few, so the ledger's "The header lists every change" is false.
- **R4-5.** A finding in round 3's own table (4.3, note 7) was answered nowhere. REFUSALS.md's `graph-form` row is still one cause short, and the ledger still says it lists every cause.

What holds up, against my own plants:
- the freeze, at the start and the end;
- the runner, 17 of 17 in a `git init` copy and in a committed clone, and `--budget quick`, 14 of 14;
- a commit and clone of all 237 files, byte for byte under both `core.autocrlf` settings;
- R3-1 in every shape I tried, on Windows and Linux;
- all fifteen of round 3's faults, which now each fail a test;
- every figure in the lead's measured block, reproduced (4.2);
- all review copies against their sources, and `round3.md` against its verifier's last message;
- NOTICE.md's statements about the record files.

## 2. Setup

- **Freeze.** MEASURED: `cd frozen/tree && sha256sum -c ../SHA256SUMS.txt` gives 237 OK and no other line. `check\freeze_check.py` (binary mode) agrees at the start and the end: 237 files on disk, 237 listed, no mismatch, no `.pyc`. Only `ParcelRound-METHOD-origin-main.md` and `terms-check-report.md`, which are not in `tree\`, are newer than `SHA256SUMS.txt`.
- **Hosts.**
  - Windows 11, Git Bash, Python 3.12.9, pytest 9.1.1, ruff 0.11.9, git 2.45.2.
  - WSL2 Ubuntu 22.04, Python 3.10.12, on the ext4 filesystem and not `/mnt/c`.
  - Wherever a probe shelled out I named Git Bash by its full path.
- **Runner.**
  - MEASURED: `QRO_MOTH_ROOT=<repos>/moth-quantum bash verify/run.sh` in a `git init` copy, run `20261015-004714-29191-nocommit+dirty`: passed 17, failed 0, skipped 0.
  - The stage counts equal the ledger's last block: docs 60, tool-tests 39, vocab-tests 7, format 520, custody 19, control-tests 15, controls-run 9 of 9 with 21 pending, study-plants 68 faults refused and 6 right variants accepted, privacy 237 files with none binary, privacy-controls 33 of 33, instruments 5 of 5, check-docs 10 documents with 21 other markdown files and 33 source files, the twin `ff3fe486…`, and the negative control refused `raw-digest at data/raw.counts.json`.
  - `--budget quick` passed 14 of 14 in 22 s wall. Without `QRO_MOTH_ROOT`, `instruments` skips by name and the run ends "PASSED, with 1 skipped by name above".
- **Commit trial.** MEASURED (`check\clone_trial.sh`): the 237 files committed in a scratch repository with a plain-sentence message, then cloned with `core.autocrlf` true and false.
  - In each clone 0 files differ from SHA256SUMS. The privacy gate reads 237 files and 1 commit message and finds nothing. `git status` is clean.
  - In the `false` clone the runner passed 17 of 17 and left the tree clean.
- **Linux.** MEASURED (WSL2 ext4, Python 3.10.12): `tests/format`, `custody`, `controls`, `vocabulary` and `tools` give 600 passed, and `tests/docs` gives 60. No test skipped.

## 3. Defects

### R4-1. The command line's tests leave four faults green

- **Where.**
  - `tests/format/test_cli.py:1-2`: "every verdict, every misuse, and every way a verdict can fail to arrive".
  - `qro/__main__.py:33-37` (the write loop), `:47-55` (both descriptors failing), `:62-64` (the flag), `:67-68` and `:72-74` (the kind tests).
  - `CLAUDE.md:43-45`, `docs/FORMAT.md:129-133` and `qro/fixture.py:4-6`: a crate naming the fixture is refused `step-unbuilt` by the command line run without `--fixtures`.
  - `__main__.py:8` and `FORMAT.md:127-128`: "a crate that is not a directory, or a log or record that is not a file, is misuse: 2".
- **What holds.** MEASURED (`check\probe_cli.py`, `probe_posix.py`, about 70 process runs):
  - A pipe nobody reads, a read-only descriptor, `>&-`, `>&- 2>&-` and `| head -c 0` all exit 3. So do `/dev/full`, `ulimit -f 0` and a full non-blocking pipe, which exist on Linux only. The accepted twin and a refused crate behave alike.
  - `python -u`, `-O`, `-OO`, `-X dev`, `-W error`, `-X utf8`, `PYTHONIOENCODING` of `utf-16` and `ascii:strict`, and `PYTHONUNBUFFERED` give the same bytes.
  - A key holding a line feed, ESC, CR, NUL or DEL prints as one escaped line. A 1,000,000-character key gives one printable line of 1,000,054 bytes. Non-ASCII crate and log names are escaped (`caf\xe9-\u4e2d-nowhere`, `no\u2028such`).
  - So R3-1's fix is right.
- **MEASURED, the faults.** `check\r3tools\mutants\m_cli4.py` through round 3's `hm.py`, and `check\demos_r4.py`, `demos_posix.py`, `demos_win2.py`. Each edit is one change to a copy. All 660 tests stay green under each. Row 1 also passes the whole runner, 17 of 17.

| # | the edit | shipped | edited |
|---|---|---|---|
| 1 | `fixture.register()` runs without the flag | `check CRATE` on the twin: exit 1, `REFUSED step-unbuilt … qro-fixture-counts` | exit 0, `ACCEPTED ff3fe486…` |
| 2 | `is_dir()` becomes `exists()` for the crate | `check FILE`: exit 2 | exit 1, `REFUSED file-missing` |
| 3 | `is_file()` becomes `exists()` for the log and records | `custody DIR`: exit 2 | exit 3, `FAILED … PermissionError` |
| 4 | the partial-write loop becomes one `os.write(fd, data)` | a 1 MB refusal into a non-blocking pipe with 64 KB of room: exit 3, `FAILED` on stderr | exit 1, 65,536 bytes of a cut line on stdout, nothing on stderr |
| 5 | the inner `except Exception: pass` becomes `raise` | `>&- 2>&-`: exit 3 for the twin and for a refused crate | exit 1 for both |

  Row 4 ran on WSL; rows 1 to 3 and 5 ran on Windows. Three more edits survive: the loop dropping a byte of a partial remainder, the second failure left unguarded, and `?` written for any character above U+FFFF.
- **A fault that shows it.** Row 1. With registration made unconditional, `python -m qro check CRATE` accepts a crate that names a generator and raw form the production checker does not have. That breaks "never let a crate pass a check that does not exist" (`CLAUDE.md:41-42`, `checker.py:14-15`). No test runs the command line on a fixture crate without the flag. `test_cli.py` always passes `--fixtures`, and `test_refusals.py` empties the registries by hand.
- **Why the lead's operators missed it.** Operator D edits comparisons, boolean operators, `not`, integer constants and statements. It has no site for "a call made unconditional", "a predicate widened", "a loop replaced by one call" or "an except branch". The lead's own 18 command-line mutants are all killed (MEASURED), and none aims at these.
- **Fix.** Four short tests:
  - the fixture crate through the command line without `--fixtures` (exit 1, `step-unbuilt`);
  - an existing directory as a log and as a record, and an existing file as a crate (exit 2);
  - `os.write` patched to take three bytes at a time, with the whole line required;
  - both descriptors broken (exit 3, no exception).
  
  Or restate `test_cli.py`'s first sentence as what it holds.

### R4-2. The spellings, the path rule and the walk: faults at 68 sites leave the suite green

- **Where.**
  - `tests/format/test_sites.py:1-4`: "so that no check can be removed with every test still green".
  - `tests/format/test_spelling.py:1`: "refuses a second spelling of the same value".
  - `docs/VALIDATION.md:99-100`: "each fix is held by a test", with the P0-1 row.
  - `docs/FORMAT.md:79-82`: `COM1` to `COM9`, `LPT1` to `LPT9`.
- **MEASURED.**
  - Round 3's class-member removal, adapted to the code as it is now with `_DEVICE` added (`m_x4b.py`, 332 mutants).
  - Two operators of my own on the spellings' regexes: quantifiers, separators and branches (`m_x7.py`, 74 mutants); and each atom made a wildcard `.` (`m_x8.py`, 75 mutants).
  - For each survivor, `check\witness.py` tries single-character substitutions of the tests' own accepted values (88,896 strings). It reports a value the edited spelling accepts, crashes on or wrongly refuses, against the shipped one.
- **In total.** 31 sites let in what the shipped code refuses. 3 more crash on it. 34 turn away what it accepts.

| the edit | survivors | what the edited code does |
|---|---|---|
| a digit dropped from `com[0-9]` (2 to 8) or `lpt[0-9]` (2, 3, 4, 6, 7, 8) | 13 of 20 | accepts `data/COM2` to `COM8`, `data/LPT2` and the rest |
| `com[019]\|lpt[0159]`, all at once | whole suite: 660 passed | a crate holding `data/COM3`, `data/LPT7.txt` and `data/com5.json`: shipped exit 1, `REFUSED spelling … a name Windows reserves for a device`; edited exit 0, `ACCEPTED c62d62f3…` (built on WSL, where the files can exist) |
| the time's two `:` written as the unescaped `.` | whole suite: 660 passed; whole runner: 17 of 17 | a crate whose `qro:writtenAt` is `2026-10-14T00x00x00Z`: shipped exit 1, `REFUSED spelling at ./ qro:writtenAt`; edited exit 0, `ACCEPTED ff3fe486…` |
| any one atom of the time pattern made a wildcard | 12 of 15 | accepts `!` for either `-`, either `:`, `Z` or the fraction's dot, and `+` for a digit (`2026-10-14T10:26:+3Z`) |
| the size's `0` or digit class made a wildcard | 2 of 3 | `!` crashes `int()`; `٢` (Arabic-Indic) is accepted as a size |
| the rational's atoms made wildcards | 5 of 9 | crashes on `0/!`, `0!1`, `!/1`; accepts `٢/1` and `8 /273` |
| the binary64's space made a wildcard | 1 of 3 | accepts `3fe0000000000000!5e-1` |
| the scheme's first class made a wildcard | 1 of 2 | `absolute()` and the `iri` spelling accept `!ttps://…` |
| any letter of `con prn aux nul com lpt conin conout` made a wildcard | 33 of 34 | refuses valid names such as `data/!ux.txt`, `data/CO!1`, `c!n` |
| step 2 follows a nested Dataset only from the root's own `hasPart` | whole suite: 660 passed | root, then `data/`, then `data/run1/`, then a file: shipped accepts; edited refuses `file-unlisted` |

  I count the following as equivalent, with no witness: the five `_DATE` wildcards (`date.fromisoformat` refuses what the pattern lets by), one `_BINARY64` wildcard, and the 76 `_BINARY64` survivors in my full sweep of `[!-~]`. No survivor is a character a valid exact decimal contains. `_ID` and the IRI tail lose no member.
- **Why round 3's operators missed it.**
  - Round 3 asked for accepted values that use every character a class admits. The lead supplied them, and note 1 holds: only `_DEVICE` has a surviving class-member removal.
  - The refused side was never swept. A class made wider, a separator made a wildcard, or a device list made one digit shorter is invisible while the suite's refused values are a handful of whole strings.
  - Round 3's row 12 asked for a nested Dataset, and `test_a_dataset_nested_in_the_root_reaches_its_files` plants one level. A walk that follows only the root's parts passes it.
- **Fix.**
  - One test over the refused side: for every accepted example of every spelling, every position, every printable ASCII character and a few non-ASCII ones, the result is refused unless an independent check says it is a member.
  - Device names: `COM0` to `COM9` and `LPT0` to `LPT9`, with and without an extension, and near-misses accepted (`cox`, `aux1.txt`).
  - One plant for a Dataset two levels down.

### R4-3. Two tests hold less than the sentence over them

- **(a) Item 8's "no count".**
  - READ: `FORMAT.md:52-54` says the test requires "no count of them". `VALIDATION.md:449` says "no count in any form". `tests/docs/test_docs.py:65-80` looks for a number word or digit only in the text before the item's first colon.
  - MEASURED (`check\probe_item8.py`, calling the test's own `p0_own_problems`): "These eight refusal names" in the lead sentence is caught. "(the fourth name)", "the eighth of eight", "(8 in all)", "Eight names in all." on its own line, "about a dozen names here" and "(three)" in the bullets each return an empty list.
  - This is R3-3(c) again: the instance is fixed, the class (a count anywhere in the item) is not.
- **(b) The negative control "names the refusal".**
  - READ: `tests/docs/test_stage_registry.py:20`, and the ledger's "a negative control that names no refusal" (`VALIDATION.md:457`). `shape_problems` (`:138`) requires only that `MUST_SAY="[^"]+"` is not empty.
  - MEASURED (`check\probe_registry.py`, only the four real gate tests, on an edited copy of `verify/run.sh`): `MUST_SAY="R"`, `"REFUSED"` and `"REFUSED file-digest"` each leave 4 passed.
  - `MUST_SAY` is what makes the control fail for the right reason. The twin, control-tests and controls-run stages would still catch a control failing for the wrong reason, which bounds the harm.
- **Fix.** (a) Scan the whole item, outside backticks and quotation marks, for number words and digits, or say "no count in the first sentence". (b) Require `MUST_SAY` to be `REFUSED ` and a name in `V.REFUSAL` equal to the control's expected refusal, or say "names something".

### R4-4. `tools/check_docs.py`'s header lists one change too few

- **READ.** The header (`:2-8`) says the rewritten docstring "drops a sentence of moth-quantum's own history". `VALIDATION.md:450` says "The header lists every change."
- **MEASURED** (diff against `git show 3a73823:tools/check_docs.py`, read only): the docstring drops two sentences.
  - One is the history sentence ("Moving the tests into stage directories left seven such names pointing at nothing …").
  - The other is "A broken link in a project about records is the cheapest possible own goal.", a rationale and not history.
  - Everything else in the diff, the header does name: directories and root documents, `FOREIGN`, the missing-index problem, links in every markdown file under `docs/` and `records/`, forward slashes, the summary's counts, "directly under docs/", and the `docs/studies/` exclusion.
- **Fix.** Name both sentences, or restore the second.
- **Below the bar, same kind.** `verify/run.sh`'s header says comments that named Quantum-Film's files are "reworded". One was deleted: the two lines above `echo "packages=…"`, which named the `golden` stage (`3a73823:verify/run.sh`, lines 168-169). The rest of that header is exact. `verify/pytest-stage.sh` differs from moth-quantum's only by its two header lines, as it says.

### R4-5. A round-3 finding left unanswered: REFUSALS.md's `graph-form` row

- **READ.**
  - Round 3, table 4.3, note 7: "one cause short: the root's `conformsTo` must be Process Run Crate 0.6 and this profile (`reader.py:185`); the row does not name it."
  - The ledger (`VALIDATION.md:347-348`): "REFUSALS.md's `graph-form` row lists every cause, step 3's among them." The round-3 entry does not answer round 3's finding. `docs/REFUSALS.md` and `qro/vocabulary.py:204` are unchanged.
  - The row lists: the top level; an entity without @id or @type; a repeated @id; case-only twins; the order; the descriptor; the root, its type and every term it must carry; the root's mentions; a reference that names no entity; a term off its domain; and, at step 3, a raw result that is not a File the crate holds.
- **MEASURED.** The omitted cause is in the code (`reader.py:183-184`) and is planted (`test_sites.py`, "a root conforming to RO-Crate only", refused `graph-form`). A `@graph` that is not a list of at least two objects (`reader.py:127`) is a second cause. The row can only be read as covering it under "the top level".
- **Fix.** Add the cause to the `Refusal` text in `vocabulary.py` and run `python tools/gen_vocabulary.py --write`.

## 4. Per scope item

### 4.1 R3-1 to R3-4

| item | verdict | evidence |
|---|---|---|
| R3-1, the command line | the code holds; the tests do not (R4-1) | The shapes under R4-1. Exit 120 no longer occurs. One limit is unstated: a partial line can arrive. MEASURED (WSL): a 1 MB line into a non-blocking pipe gives exit 3, `FAILED` on stderr, and 65,536 bytes of the line on stdout. An `ACCEPTED` line is 73 bytes and goes in one write. |
| R3-2, fifteen faults | holds | MEASURED (`m_rows.py` through `hm.py`, 17 edits for the 15 rows, written against the code as it is now): each fails a test. See below for the variants. |
| R3-3(a), the mask check | holds for shell syntax | MEASURED: 24 masks and a continuation line are caught. Not caught: a tool's own mask, and a stage call the shell does not run (notes 1 and 2). |
| R3-3(b), the stream sentence | holds | MEASURED (round 3's `exp_absolute.py`, 26 ids, whole checker): `README:hidden`, `LICENSE:x`, `Makefile:x`, `data:x`, `ab:x`, `a+b:x` and `README:$DATA` have `absolute()` true. `notes.txt:hidden`, `data/README:hidden`, `C:/x.txt`, `a:x`, `c:x`, `7z:x`, `_x:y`, `iris.beep:x` and `x:$DATA` are refused `spelling`. FORMAT.md item 11 and `absolute()`'s docstring say so. |
| R3-3(c), item 8 | one instance fixed, the class not | R4-3(a). |
| R3-4, the copies and headers | the copies hold, one header is short | 4.6; R4-4. |

For R3-2's variants, I made 25 edits of my own at the rows. 22 are killed. The three survivors:
- `check_log` moved after the head test: the same accepts and refusals, and only the name of a double fault changes (equivalent).
- `hasPart` as a non-list: the reader never lets one through (equivalent).
- The walk two levels deep: real (R4-2).

The alphabet losses of row 11 were 94 mutants: 93 killed, and the 94th does not compile. Its twin in `m_x5` is killed.

### 4.2 The mutation tests

I ran every mutant against the six directories the runner runs (660 tests). A survivor then ran against the twin, the negative control, `gen_vocabulary --check`, `controls.run`, `check_docs` and ruff. Round 3's `hmp.py` and `hm.py` count a pytest failure as a kill, and so a hang killed at 300 s.

| operator | over | mutants | killed | survived | equivalent | real gaps |
|---|---|---|---|---|---|---|
| D, round 3's `ast_gen.py` and `hmp.py` | reader 111, checker 85, custody 46, spelling 127, canonical 29, `__main__` 56 | 454 | 443 | 11 | 11 | 0 |
| round 3's command-line set (`m_x3`) | `__main__` | 37 | 10 | 1 | 1 | 0 (26 not applicable) |
| the lead's command-line mutants (`p0\m_cli.py`) | `__main__` | 18 | 18 | 0 | | |
| path alphabet, one character (`m_x1`, `m_x5`) | `_SEGMENT` | 99 | 97 | 1 | 1 | 0 (1 does not compile) |
| path and reader variants (`m_x2`) | spelling, reader | 39 | 36 | 3 | 3 | 0 |
| class-member removal, round 3's list of 372 from its old source (`m_x4`) | spelling, reader | 372 | 232 | 8 | 8 | 0 (132 not applicable) |
| the lead's scheme and IRI-tail removal (`p0\m_scheme.py`) | spelling | 210 | 210 | 0 | | |
| class-member removal, adapted, `_DEVICE` added (`m_x4b`) | spelling | 332 | 311 | 21 | 8 | 13 |
| every member of `[!-~]` in `_BINARY64`, `_ID`, the IRI tail (`m_x6`) | spelling | 282 | 206 | 76 | 76 | 0 |
| round 3's 15 rows and my 25 variants (`m_rows`) | `qro/` | 42 | 39 | 3 | 2 | 1 |
| my command-line mutants (`m_cli4`) | `__main__` | 16 | 7 | 9 | 1 | 8 |
| quantifiers, separators, branches (`m_x7`) | spelling | 74 | 70 | 4 | 2 | 2 |
| each atom a wildcard (`m_x8`) | spelling | 75 | 15 | 60 | 6 | 54 |
| round 2's list (`m_r2`) | spelling, reader, checker | 68 | 49 | 4 | 4 | 0 (15 not applicable) |
| the lead's earlier list (`m_lead`) | spelling, reader, `__main__` | 29 | 22 | 0 | | 0 (7 not applicable) |

That is 2,147 mutants in all.

**The lead's measured block against my runs.** Every figure reproduces:
- D: 454 mutants, 443 killed, 11 survivors.
- Round 3's path set: 39, with 36 killed.
- Its alphabet sets, 94 and 5: all killed but a gain of `/` and one that does not compile.
- Its class-member removal: 372, with 232 killed, 132 not applicable and 8 survivors.
- The lead's scheme and tail removal: 210 of 210.
- Round 3's command-line set: 26 not applicable, 10 killed, 1 survivor.
- The lead's 18 of 18.

The block says its survivors are equivalent, and for these sets that is right. Its operators do not reach R4-1 or R4-2.

**D's eleven survivors, with the argument.**
- `reader.py:40`, `seen.add(k)` deleted. A repeated key fails the re-serialisation with the same name, `spelling`. The location text differs and the verdict does not.
- `reader.py:127`, `2` to `1`. A one-entity graph is refused `graph-form` at `@graph` a few lines later.
- `spelling.py:47`, `>> 62` for `>> 63`. The test is on truthiness, and the two zeros give 0 and 2.
- `spelling.py:49`, three times (`>` to `>=`, and `0` to `1` or `-1`). The branch sees only infinities.
- `spelling.py:95`, a size of 20 digits. Any 20-digit decimal exceeds 2^63 - 1 and fails the next test.
- `__main__.py:30`, twice. Space and `~` pass through `unicode_escape` unchanged.
- `__main__.py:50`, `3` to `4` or `2`. The second write goes to the descriptor that has just failed.

Two further D results are not survivors but are worth stating:
- `spelling.py:68`, `q = Fraction(q)` deleted, is killed by lint only. `rational` is called with an `int` or a `Fraction`, and both have `numerator`.
- `__main__.py:37`, the loop's body deleted, is a kill by hang. MEASURED (`check\hang_check.py`): no result after 60 s. The runner has no timeout.

My own equivalent survivors are these: the `hasPart` list guard; `check_log` after the head test; `_BINARY64`'s `+` to `*`; `_DEVICE`'s `(\..*)?` to `(\..+)?` (the trailing-dot rule runs first); the five `_DATE` wildcards; and the registration moved below the usage test.

### 4.3 Round 3's notes 1 to 15

| note | as the ledger says? | evidence |
|---|---|---|
| 1, the accepted side | taken; holds for the accepted side | MEASURED (4.2): only `_DEVICE` has a surviving class-member removal. The refused side is R4-2. |
| 2, registry plants | taken; the four plants are caught, one wider than its test | R4-3(b). |
| 3, camelCase tokens | taken; holds | MEASURED: `named:camelToken` and its plant; `privacy-controls` 33 of 33. |
| 4, the acknowledgement | not taken; stated | READ: in NOTICE.md the second sentence is outside the quotation marks; the README's is unquoted. |
| 5, the device names | taken; holds | READ: FORMAT.md item 11 and the comment in `spelling.py`. |
| 6, path length | taken; holds | READ: FORMAT.md's last bullet. |
| 7, item 7 | taken; holds | MEASURED: `HEADER_KEYS` is six terms. Five stand on the root, and `qro:implementation` on `*`. |
| 8, the registry docstring | taken; holds | READ: it says `check_*.py`, and the code reads that. |
| 9, the study's status line | not taken; stated | READ: "Draft 12, 2026-10-14 … Nothing here is built yet." P0 was built the same day, and the README says so. The limit sits in the ledger and README, not in the study. |
| 10, `--list` | taken; holds | MEASURED. |
| 11, a missing path | taken; holds for a missing path | MEASURED: a missing log, record or crate exits 2. Wrong-kind paths are untested (R4-1). On Linux a 300-character name exits 3, "File name too long", not 2. |
| 12, timings | not taken; fair | MEASURED: quick 22 s wall (18 s of stage time); full about 65 s of stage time. |
| 13, a FIFO | not taken; the sentence is false | The ledger says "No host here can make a FIFO." MEASURED on WSL2 ext4 (`check\probe_fifo.py`): a FIFO at the top, in `data/` and two levels down, a Unix socket, a file link and a dangling link are each refused `file-link` without blocking. A FIFO as the metadata file is refused `file-missing`. |
| 14, the docs gate | taken; holds | MEASURED: 10 documents and 21 other markdown files, every link resolving. `qro/data/README.md` is outside `docs/` and `records/` and is not link-checked. |
| 15 | nothing to take | |

Round 3's table-4.3 note 7 about REFUSALS.md is R4-5.

### 4.4 The changes beyond round 3's findings

- **`SCHEME` shared by `absolute()` and the `iri` spelling.**
  - It holds: one pattern, one definition. The lead's 210 mutants are killed; my wildcard on the first class is not (R4-2).
  - It wrongly refuses, and says so, a dotted or one-letter scheme (`com.example:x`, `x:y`), both RFC 3986-legal. READ: FORMAT.md item 11, `vocabulary.py`'s `iri` text and the generated VOCABULARY.md state it. No term uses the `iri` spelling (MEASURED), so no crate is refused for it today.
  - The ledger says "the code has one meaning of an absolute IRI". MEASURED: `absolute("http:")` is true and `problem("iri", "http:")` refuses it, since the spelling needs a non-empty tail. The scheme is shared; the meaning is not.
- **The registry counts a tool or a directory as staged only as a stage's program.**
  - It holds: planted four ways for a tool and once for a directory. The real gate tests also catch `python3`, a duplicate stage name, the twin planting another plant, and the vocabulary stage run as `--write`.
  - It wrongly flags legitimate forms outside its grammar (`python3`, `python -u`, `--ignore=` of a file). That is safe, and its grammar is in the docstring.
  - Its limits are not stated: notes 1 and 2.
- **A crate that is not a directory, or a log or record that is not a file, is misuse.**
  - It holds for a path that does not exist. For the other kinds, see R4-1.
  - It wrongly refuses, without saying so, a log given as a pipe or process substitution (`custody <(…)`). MEASURED: a FIFO as the log exits 2, "no such file".
  - A symbolic link to a crate is followed and accepted (MEASURED). A link to a log is followed too (BELIEVED: `is_file()` follows links).

### 4.5 Anything else in the tree that is now false

- R4-4 and R4-5, and the note-13 sentence (4.3).
- **The ledger's older N8 line** (`VALIDATION.md:197-200`): "a stream's name, with its `:`, is refused at step 1, `spelling`". R3-3(b) showed it false for a top-level name that is a scheme (`README:hidden`). The round-3 entry's "Corrections to the entries before" does not list it. FORMAT.md states the limit correctly.
- **`CLAUDE.md:51-52`**, "A crash is never a verdict." MEASURED: `python -m qro check …` run where `qro` cannot be imported prints "No module named qro" and exits 1, the refusal's code, with nothing on stdout. The sentence holds for the checker's code, not for starting it.
- **The ledger's R3-1 row** says the tests plant "each case, in process and as a process". As a process only the pipe is planted. The closed descriptor is planted in process only, with descriptor 10^6. The code behaves alike for both (MEASURED).
- CLAUDE.md, README.md, NOTICE.md and `docs/README.md` otherwise agree with the code and files. MEASURED against the records: 65 job files and 7 snapshots; no `user_id`, `cost`, `estimated_running_time_seconds`, `circuits_execution_time_ns`, instance or plan id appears in any record or probe.

### 4.6 The review copies

- **Copy against source.**
  - MEASURED (`check\review_check4.py`, my line-level check from round 3's, run on all 16 files).
  - Every study copy equals its source after the stated changes, with 0 unexplained lines.
  - The per-file CRLF counts (291, 395, 226, 202, 270, 172, 131), the wrapper yes/no, the final-line-feed column, the home-path counts (1, 1, 0, 0, 1, 1, 0, 1, 1, 0, 0, 1) and all twelve SHA-256 prefixes equal the README's.
  - The seven wrapped files hold the nine tags the README lists and 44 raw angle brackets each, all in the wrapper (`measure_r3.py`). No report body holds one.
  - The P0 copies hold 4 `<a home path>` redactions in round 1's interim, 1 in round 1's final, and one redacted home path in round 2, as the README says. Round 3's copy equals its source byte for byte (SHA-256 `5c361d20…`).
  - My check reported 3 unexplained lines in the two round-1 copies. All three are lines where a verifier quoted a home-path shape (UNC and `%2F` forms) that my loose "looks like a path" test does not recognise. `review_debug.py` shows the copy has `<a home path>` where the source has the shape, so they are explained.
  - `round2.md` and `round3.md` already hold placeholders their verifiers wrote (`<a home path>` in both, `<repos>` in round 3). The README's "0" for round 3 counts the lead's redactions, not the placeholders in the file. It does not say so.
- **Source against verifier.** MEASURED (`sources_vs_transcripts4.py`, `tx_last.py`).
  - 11 of the 12 study sources equal the last long message of a subagent transcript, and the task id in each wrapper names it. The twelfth, draft 4's, is the lead's transcription, as its row says.
  - Round 1's interim equals the first of its verifier's two long messages, and its final the last, with the transport's `&lt; &gt; &amp;` undone.
  - `round3.md` is its verifier's final message. The transcript's last assistant record has stop reason `end_turn` and one text block of 35,968 characters. That text stripped, plus one line feed, equals the staged source, and the placed copy equals the source.

## 5. Notes (below the bar of a defect)

1. **The registry cannot see a stage the shell does not run.** MEASURED (`probe_registry.py`, four real gate tests): `if false; then stage … fi`, a here-doc comment (`: <<'EOF'`), an `exit 0` before a stage, and `[ -n "$X" ] &&` ahead of a stage each leave 4 passed, though the stage runs nothing. `CLAUDE.md:17-18` says the registry fails a tool's check "that no stage runs". It holds for a stage that is absent or commented out.
2. **A simple command can be a tool's own mask.** MEASURED, unseen: `ruff check … --exit-zero`, `check_privacy.py --help`, `gen_vocabulary.py --check --help`, and `check_study.py` without its second argument. The word alphabet admits all of them. The docstring lists shell constructs only, and is exact about those.
3. **Nothing watches the runner's own exit.** An edit removing the `exit 1` after "== FAILED" leaves the registry green. No test runs `run.sh` against a failing stage. A `stage()` that ignores `rc` is caught at run time by the negative control.
4. **A partial line can arrive with exit 3** (4.1). The exit code says the verdict did not arrive; stdout may hold its first 65,536 bytes.
5. **A user error can still exit 3.** MEASURED: a crate name over 255 characters on Linux is `FAILED: the checker itself failed, OSError`. BELIEVED: so is a parent directory the user cannot search, since `Path.is_dir()` raises `PermissionError`. Windows gives 2 for the names I tried.
6. **`absolute("http:")` and the `iri` spelling disagree** on an empty tail (4.4). No term uses the spelling.
7. **An import-time failure exits 1** (4.5): a wrong working directory, a broken module or an older Python.
8. **REFUSALS.md's other rows are summaries.** `file-missing` omits a missing metadata file. `file-digest` and `raw-digest` omit a missing sha256 or contentSize. `raw-form` omits a raw result naming no form. Only `graph-form` enumerates, so only it is a claim.
9. **The ledger's "P0-1 … each fix is held by a test"** holds for the year field of a time and a date, with Arabic-Indic and fullwidth digits. The wildcard mutants show the month, day, hour, minute and second fields are not held by a refused value. BELIEVED: a wide class there would need both `re.ASCII` dropped and `[0-9]` widened, which is why this is a note.
10. **A registered parcel's code that raises `SystemExit(0)` ends the process with exit 0 and no line**, since `except Exception` does not catch it. Parcels are trusted code, so I rate it a limit.

## 6. What I did not do

- **No macOS, and no real Windows console.** A console handle for stdout could not be driven from here. Linux is WSL2 with Python 3.10.12, not 3.12.
- **No mutation of `controls/`, `tools/` or the tests.** I mutated `qro/`. I edited `verify/run.sh` and FORMAT.md in copies for the registry and item-8 probes. I probed `tools/check_privacy.py` only through the lead's controls (33 of 33).
- **No IBM or Atlas contact; no qiskit import; nothing submitted.** I did not open `~/.quantum-film`, any `.atlas` directory, or any key, token or CRN. I read moth-quantum only by `git show` and as the runner's `QRO_MOTH_ROOT`. Every key-shaped string in my scripts is made up.
- **I did not re-read IBM's or Moth's terms.** NOTICE.md is checked against the record files, not against the terms report.
- **No fuzz at round 3's scale** (2,000,000 path ids, 126,475 byte-level mutants of the twin). `reader.py` changed only in `absolute()`, whose pattern is the same text as before (READ, diff against round 3's tree), so I relied on round 3's runs.
- **No `rocrate-validator`, no JSON-LD processor, no review of P1 to P5.**
- **I read the verifiers' subagent transcripts** only to compare messages. I printed no text from them.
- **Slips of mine.**
  - My first listing of the frozen tree printed the file names under `records/`, which contain IBM job ids, as round 3's did. I printed none after that, and this report names none.
  - A Python heredoc lost a backslash on first use, as CLAUDE.md warns. I wrote every script to a file after that.
  - My first registry probe ran the lead's plant tests too. They fail whenever my edit changes the text they replace, so I reran with only the four real gate tests.
  - One shard of `m_x8` died on a cp1252 decoding error in my harness copy. I reran its 12 mutants with a UTF-8 decode.
  - Stray `.pyc` files appeared in my own pristine copy `base\`, and I could not trace which script wrote them. `frozen\` never held one. I removed them and re-checked `base\` against SHA256SUMS.
- **No one was contacted, and no banner accepted.**

A scoped re-check after the fixes should re-run operator D, the command-line set with the five edits of R4-1, `m_x4b`/`m_x7`/`m_x8` with `witness.py`, and the probes `probe_registry.py` and `probe_item8.py`. I will pick my own faults again.
