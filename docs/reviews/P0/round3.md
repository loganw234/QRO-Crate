The harness refused the file write, as it did for round 2, so this message is the report.

# P0 verifier, round 3: scoped re-check

The harness refused my write of `SCRATCH\verifier-P0-r3\report.md`, so this message is the record. My scripts, logs and mutant lists are in `SCRATCH\verifier-P0-r3\check\`. Nothing in `frozen\` or in the real repository was edited.

## 1. Verdict: NOT READY

There are four defects. None needs a redesign. The shipped code gives no wrong accept today. Each defect is a sentence that claims more than the code does, or a check that the suite lets a fault through. ParcelRound's section 6 says the second kind is worth as much as a defect, because it is the defect of the next change.

- **R3-1.** The command line's claims about its output are false in cases I measured. A verdict that cannot be written exits 120, not 3. A crate's key holding a line feed makes the command print a second line that starts with ACCEPTED, with exit 1.
- **R3-2.** The ledger's "a fault aimed at each check" is false. Fifteen faults of mine, each one edit to a correct check, leave all 471 tests green. Ten give a wrong answer or crash on hostile input. Five turn a valid crate away.
- **R3-3.** Three limits are stated by an instance, and the class walks past them: the registry's mask check (`|| true`), FORMAT.md's stream sentence (`notes.txt:hidden`), and item 8's "holds this list to the table".
- **R3-4.** Statements about what was changed or copied are each one item short: the QRO-0 review README (three places) and the header of `tools/check_docs.py`. The ledger's "state every change" and "lists every change" are therefore not exact.

What holds up, against my own plants:
- The freeze; the runner (three full runs, 17 of 17 each, one of them in a committed clone); a commit and clone of all 235 files, byte for byte under both `core.autocrlf` settings.
- The lead's measured block, which my runs reproduce to the figure (4.2).
- R2-3, R2-4, R2-5 and R2-7 in full; R2-1, R2-2, R2-6, R2-8 and R2-9 for the instances round 2 named.
- The `text` spelling, against all 1,114,112 code points; the path rules, against 2,000,000 random ids; 126,475 byte-level mutants of the twin (0 crashes, 0 second spellings); 14,768 look-alike mutants (0 accepted).
- All 15 review copies against their sources, and each source against its verifier's own last message.
- NOTICE.md against the IBM text the research agent extracted.

## 2. Setup

- **Freeze.** MEASURED: `cd frozen/tree && sha256sum -c ../SHA256SUMS.txt` gives 235 OK and 0 not OK, at the start and at the end. `check\freeze_check.py` agrees. The file sets are equal and there is no `.pyc`. No file in `frozen\` is newer than `SHA256SUMS.txt`.
- **Live tree.** MEASURED (`check\live_vs_frozen.py`, read-only): the real repository's files, leaving out `.git` and `.gate-state`, are the same 235, byte for byte. Its `docs/VALIDATION.md` carries a later modification time with identical bytes.
- **Hosts.** Windows 11, Git Bash, Python 3.12.9, pytest 9.1.1, ruff 0.11.9, git 2.45.2. For POSIX checks: WSL2 Ubuntu 22.04 (Linux 5.15), Python 3.10.12, pytest 9.1.1, running copies under my own directory.
- **Runner.**
  - MEASURED: `QRO_MOTH_ROOT=<repos>/moth-quantum bash verify/run.sh` in a `git init` copy, run `20261014-223403-20664-nocommit+dirty`: passed 17, failed 0, skipped 0.
  - A second full run took 64 s and passed 17 of 17. `--budget quick` passed 14 of 14 in 17 s.
  - A committed, clean clone (commit b2f30ef) passed 17 of 17, and `git status` was clean afterwards.
  - The stage counts equal VALIDATION.md's last block: docs 23, tool-tests 38, vocab-tests 7, format 370, custody 18, control-tests 15, controls-run 9 of 9 with 21 pending, study-plants 68 and 6, privacy 235 files with none binary, privacy-controls 32 of 32, instruments 5 of 5, check-docs 10 documents and 32 source files, twin `ff3fe486…`. The negative control was refused `raw-digest at data/raw.counts.json`.
- **Strict warnings and order.** MEASURED: `python -X dev -W error -m pytest -q tests` gives 471 passed; `ruff check qro controls tools tests` is clean. Each of the 12 test files alone, and all files in reverse order, give 471 passed.
- **Commit trial.** MEASURED (`check\clone_trial.sh`): the 235 files committed in a scratch repository and cloned with `core.autocrlf` true and with false. In each clone 0 files differ from SHA256SUMS, and the privacy gate reads 235 files and 1 commit message and finds nothing. With `.gitattributes` removed, 230 of 235 differ.
- **Linux.**
  - MEASURED (WSL2, Python 3.10.12, a Windows-mounted and so case-insensitive directory): `tests/format` gives 370 passed, 0 skipped. The other five directories give 101 passed.
  - Real symbolic links (a file, a directory, a dangling one, one at the crate's top) are each refused `file-link`.
  - A hard link to an outside file with the same bytes is accepted, as FORMAT.md states.
- **Reused from round 2.** `mut_r2.py` and `mut_names.py` unchanged; the mutant lists of `mut_canon_r2.py` and `r3_mutants.py` through my own harness `hm.py`; `corpus_verdicts.py` (temp directory redirected into mine); `fuzz_reader.py`, `fuzz_custody.py`, `fuzz_lookalike.py`. I read each before running it.

## 3. Defects

### R3-1. The command line's claims about its output are false in measured cases

- **Where.** `qro/__main__.py:10-12` (the docstring) and `:21-38`; `docs/FORMAT.md:112-114` (item 16); `docs/VALIDATION.md:305` (the R2-2 row: a verdict it cannot print at all exits 3) and `:391-394`.
- **READ.**
  - The sentences say a refusal that echoes the crate's own text prints it escaped, and a verdict the command cannot print at all exits 3.
  - The planted test, `test_a_verdict_that_cannot_be_printed_exits_3`, replaces `sys.stdout` by an object whose `write` raises.
- **MEASURED, exit codes** (`check\exp_cli2.py` and by hand).
  - `python -m qro check --fixtures CRATE | head -c 0` on Windows prints "Exception ignored in … name='<stdout>' … OSError: [Errno 22]" and exits 120. It does so for the accepted twin and for a refused crate alike.
  - On Linux, `> /dev/full` (No space left) and the closed pipe (Broken pipe) both exit 120, for both crates.
  - With descriptor 1 closed (`>&-`), nothing is printed, and the exit is 0 for the twin and 1 for the refused crate.
  - The same refused crate under `python -u` (line-buffered, as a terminal is) exits 3, as the claim says.
  - So the claim holds for a terminal and for the planted fake. On a pipe or a file, `print` does not fail. The failure comes at the flush at exit, after `main` has returned.
- **MEASURED, control characters** (`check\exp_cli.py`).
  - A crate whose root carries the key "x", a line feed, "ACCEPTED" and 64 zeros is refused `term-unknown` with exit 1. Its stdout has two lines, and the second begins ACCEPTED.
  - A key with ESC [2J, a carriage return or a NUL is printed raw. Only non-ASCII characters are escaped.
- **A fault that shows it.** The commands above.
- **Why it matters.**
  - Exit 120 is outside the contract the docstring states (0, 1, 2, 3).
  - The exit code never reads as an acceptance, so this is not a wrong accept. But a reader of stdout can be handed a forged ACCEPTED line by a crate it audits.
  - This is P0-2's and R2-2's class again. The fix closed the instance (a character the console lacks) and not the class (a verdict the command cannot deliver faithfully).
- **Fix.** Flush inside the `try`, and treat a missing or closed stdout as exit 3. Escape C0 controls and DEL in `say`. Or restate the three sentences as what they hold.

### R3-2. "A fault aimed at each check" is false: fifteen faults leave all 471 tests green

- **Where.** `docs/VALIDATION.md:171`: "tests/format/test_sites.py plants a fault aimed at each check: 51 plants". This answers round 1's N1, whose aim was that no check can be removed with every test green.
- **Why the lead's operators did not see it.** Round 2's operator A only edits `if … raise Refused` and `return "<problem>"` sites. It has 0 sites in `qro/canonical.py` and `qro/__main__.py`, and none where a check is a call, a comparison or an argument test. The lead's measured block is right (4.2); its reach is the question.
- **MEASURED.** Each row is one edit to the shipped code, made in a copy. The whole suite (six directories) gives 471 passed under each edit. The shipped code gives the right answer in every row. The scripts are `check\demos.py`, `demos2.py`, `demos3.py`, `demos4.py` and `demo_b.py`.

| # | the check (file:line) | the one edit | what the edited code then does |
|---|---|---|---|
| 1 | `custody.check_record` checks its log (`custody.py:119`) | `check_log(log_data)` deleted | a record is accepted against a log whose second line does not chain; shipped: `custody-chain` at log line 2 |
| 2 | the CLI's custody command checks its log (`__main__.py:54`) | `head = custody.check_log(log)` becomes `head = 'none'` | `custody BROKEN.log` exits 0 and prints "ACCEPTED head none" |
| 3 | the CLI's custody command checks each record (`:55-56`) | the `check_record` call becomes `pass` | a record whose head matches no line is accepted, exit 0; shipped: `custody-head`, exit 1 |
| 4 | the CLI's misuse exits (`:42`, `:47`, `:59-65`) | the last `return usage()` becomes `return 0`; or `len(args) != 1` becomes `< 1` | `python -m qro bogus` exits 0; `check A B` checks only A and exits 0 though B is refused (shipped: exit 2) |
| 5 | the CLI prints the crate's identity (`:50`) | the digest reversed | a wrong digest after ACCEPTED, exit 0 |
| 6 | a raw-form count is a whole number of shots (`checker.py:124`) | `held < 0` becomes `held < -1` | a raw-form reader that counts -1 shots is accepted |
| 7 | the `@graph` guard (`reader.py:129`) | the first `or` becomes `and` | `@graph` given as 7, null, true or 1.5 raises TypeError (exit 3) in place of `graph-form`; 18 documents of a 3,224-document corpus |
| 8 | the path rule reaches any File (`reader.py:156`) | applied only when `@type == "File"` | a raw result (File and `qro:RawResult`) at `data/a%20b.counts.json` passes the reader |
| 9 | the device, trailing-dot and length rules (`spelling.py:163-166`) | applied to the last segment only | `data/aux/x.txt` and `con/y.txt` accepted end to end by the checker |
| 10 | the device rule's extension (`spelling.py:150`) | extension must start with a letter | `data/aux.1`, `NUL.7z` and `con.123` accepted |
| 11 | the path alphabet (`spelling.py:32`) | any one of 36 of the 62 letters and digits dropped (z, Z, 7 …) | a crate holding `data/zeta.txt` is refused |
| 12 | step 2 walks `hasPart` (`checker.py:97`) | `todo.append(ref["@id"])` becomes `pass` | a root that lists a `data/` Dataset which lists the files is refused `file-unlisted` |
| 13 | step 2 meets a part with no entity (`checker.py:94`) | `e is not None and` becomes `or` | a root `hasPart` naming a web-based file with no entity crashes (AttributeError) |
| 14 | the graph minimum (`reader.py:129`) | `< 2` becomes `< 3` | a crate of a descriptor and a root is refused |
| 15 | the size bound (`spelling.py:92`) | `<= 19` becomes `< 19` | the size 9223372036854775807 (2^63 - 1) is refused |

- **How many.**
  - Operator D (mine, in 4.2) leaves 32 real survivors, 17 of them in the command line. My command-line set leaves 18 of 37.
  - Rows 1 to 10 give a wrong answer or crash. Rows 11 to 15 turn a valid crate away. Nested Datasets (row 12) are what RO-Crate profiles normally write.
- **Fix.**
  - Three subprocess tests of the command line: the documented `check CRATE`, `custody LOG RECORD`, and each misuse.
  - One plant for each other row. A negative count, a non-list `@graph`, a web-based part, a nested Dataset, a two-entity crate, a 19-digit size, and a device name in a middle segment are each a few lines.

### R3-3. Three limits are stated by an instance, and the class walks past them

METHOD.md section 5 says a limit stated by its instances is walked past, and a limit such a fault walks past claims more than is true.

- **(a) The registry's mask check.**
  - `tests/docs/test_stage_registry.py:13` and `docs/VALIDATION.md:331` state that no stage masks its command's exit, with `|| true` as the example.
  - MEASURED (`check\exp_registry.py` and `check\plant_registry3.py`, which edit a copy of `verify/run.sh` and run only the real gate tests): `|| true`, `|| :`, `; true`, `;true` and `||true` are caught.
  - Unseen: `|| exit 0`, `|| echo ok`, `|| /bin/true`, `|| (true)`, `|| { true; }`, `|| test 1`, `|| [ 1 ]`, `|| python -c pass`, `&& true`, `| tee /dev/null`, `|| sh -c true`, a mask on a continuation line, `set +e;`, and even `|| true # fine`.
  - Round 2's note 1 was the instance `|| true`. It is fixed. The class is not.
- **(b) FORMAT.md's stream sentence.**
  - `docs/FORMAT.md:83-86` says a stream (`notes.txt:hidden`), even at the crate's top, is read as a path and refused. That holds for a stem with a dot. For a top-level stem without one, `absolute()` reads the id as an IRI.
  - MEASURED (`check\exp_absolute.py`): `README:hidden`, `LICENSE:x`, `Makefile:x`, `data:x`, `README:$DATA` and `a+b:x` have `absolute()` true and pass steps 1 to 3. The fixture's step 9 then refuses them because it regenerates the metadata; a generator that wrote them would not.
  - `notes.txt:hidden`, `data/README:hidden`, `C:/x.txt`, `a:x`, `7z:x` and `iris.beep:x` are refused `spelling`.
  - No digest may stand on such an id (its domain is a held file), so this is not a bypass of a check. The sentence is what overreaches.
- **(c) Item 8's list.**
  - `docs/FORMAT.md:51` says the test holds the list "to the table and the study".
  - MEASURED (`check\exp_registry.py`): a name the table does not have, a name the study owns, and a count worded "These eight names" each pass `p0_own_problems`. The test holds the list from below only: every own name must be there, and a count in digits or "Eight refusal names" is caught.
  - Item 8 also names four study-owned refusals as references, so a strict two-way check would need to allow them.
- **Fix.** Restate each as the class it concedes, or close the class.
  - (a) Catch any command after `||` that is not itself a check, or state the limit.
  - (b) Say "a stream on a name with a dot, or beginning with a non-letter".
  - (c) Say "contains every own name and states no count".

### R3-4. Statements about what was changed or copied are one item short

- **The QRO-0 review README** (`docs/reviews/QRO-0/README.md:6` and `:10`).
  - It lists the wrapper's contents as the task id, output file, status, summary, note and usage. MEASURED (`check\wrapper_skeleton.py`, `wrapper_strip.py`): all seven wrapped sources also carry `<tool-use-id>`.
  - It says the report inside is kept whole, "its first and last blank lines aside". MEASURED: in all seven the body has no leading or trailing whitespace, so nothing is stripped. The placing script does `strip() + "\n"`, which adds one final line feed. Each copy ends in a line feed the report inside does not have, a change the README does not state.
  - It says no source holds a raw `<` or `>`. MEASURED (`check\angle_count.py`): the seven wrapped files hold 48 each, all in the wrapper. The report text holds none, in all twelve.
- **`tools/check_docs.py:2-5`.**
  - The header lists five changes from moth-quantum's file at 3a73823.
  - MEASURED (diff against `git show 3a73823:tools/check_docs.py`): the five are all there. The docstring's own text was also rewritten: a history sentence dropped, "directly under docs/" added, and an exclusion for `docs/studies/` added.
  - The `verify/run.sh` header, by comparison, lists even reworded comments, and is exact apart from note 10.
- **The ledger.** `docs/VALIDATION.md:311` ("Both READMEs state every change, counted per file") and `:312` ("Each lists every change") are short by the items above.
- **Fix.** Add the item to each sentence. The copies themselves are right.

## 4. Per scope item

### 4.1 R2-1 to R2-9, with my own plants

| item | verdict | evidence |
|---|---|---|
| R2-1, the path rules held by a test | fixed for round 2's mutants; the family still has gaps (R3-2 rows 8 to 11) | MEASURED: every one of round 2's mutants is killed (its 68: 50 killed, 4 equivalent survivors, 14 whose text changed; the lead's 29: 29 killed). Per character, all 15 punctuation losses and all 17 gains (every printable character outside the alphabet but `/`) are killed, but 36 of the 62 letter and digit losses survive. Of 39 variants of mine, 12 survive: 3 equivalent, 9 real (the rules on middle segments, the device extension, a File of two types, a File with a `#` id). The figures VALIDATION.md quotes are exact: 24 accepted, 52 refused, 48 planted in a crate. |
| R2-2, a verdict that cannot be printed | the instance holds; the class does not (R3-1) | MEASURED: in process, a lone surrogate, a CJK character and a latin-1 character through cp1252, UTF-8 and ASCII all print escaped with exit 1. As a process, `PYTHONIOENCODING` of ascii, cp1252, utf-16 and `ascii:strict`, `PYTHONUTF8=1` and `-X utf8` all print escaped, exit 1. Misuse gives 2 and a missing log gives 3. |
| R2-3, an id is not a type | holds | MEASURED (`check\exp_domain.py`): 12 id tokens (every domain token, every type) times 28 terms is 336 crates through the whole checker, with a generator that returns the crate's own body. None is accepted off its domain. The lead's six plants are held. |
| R2-4, the format stage off Windows | holds | READ: `link_dir` plants a junction on Windows and a symlink elsewhere, with no skip. MEASURED on Linux: 370 passed, 0 skipped. `pytest-stage.sh` fails a stage on a planted skip, an xpass and an empty directory, and passes on warnings only. |
| R2-5, C1 controls | holds | MEASURED (`check\exp_text.py`): for each of the 1,114,112 code points, `text` refuses exactly the category Cc except the line feed, and the lone surrogates. 0 disagreements with the prose. |
| R2-6, a count of names | the count is gone; the list is checked from below only | R3-3(c). |
| R2-7, the Process Run Crate terms | holds | MEASURED (`check\exp_domain.py`): `instrument`, `object`, `result` and `agent` on a CreateAction give `field-kind`, as do `actionStatus` and `error`. An entity typed `Profile` gives `term-unknown`. FORMAT.md's two limits are true. |
| R2-8, the review READMEs | the counts hold; three sentences are short | 4.6 and R3-4. |
| R2-9, the "copied" headers | `verify/run.sh` exact apart from one space; `tools/check_docs.py` short | MEASURED by diff against moth-quantum's files at 3a73823. `pytest-stage.sh`'s "unchanged below this line" is true: only the two header lines differ. R3-4 and note 10. |

### 4.2 The mutation tests

Every mutant ran against the six directories the runner runs (471 tests). A survivor then ran against the twin, the negative control, `gen_vocabulary --check`, `controls.run`, `check_docs` and ruff.

| operator | over | mutants | killed | survived | equivalent | real gaps |
|---|---|---|---|---|---|---|
| A, a check made never to fire (round 2's `mut_r2.py`, round 1's site definition) | reader 32, checker 16, custody 8, spelling 17 (canonical and `__main__`: 0 sites) | 73 | 71 | 2 | 2 | 0 |
| A, with `return f"…"` problems also counted | spelling 22 | 78 | 76 | 2 | 2 | 0 |
| B, a refusal's name swapped (`mut_names.py`) | reader 35, checker 17, custody 9 | 61 | 61 | 0 | | |
| C, round 2's hand mutants (`mut_canon_r2.py`'s list) | canonical, custody, spelling, reader, checker | 68 | 50 | 4 | 4 | 0 (14 not applicable: text changed) |
| C, the lead's re-written and new (`r3_mutants.py`'s list) | spelling, reader, `__main__`, privacy | 29 | 29 | 0 | | |
| the command line (mine) | `__main__.py` | 37 | 18 | 19 | 1 | 18 |
| D, comparisons, and/or, `not`, integer constants, statement deletion (mine: `ast_gen.py`, `hmp.py`) | reader, checker, custody, spelling, canonical, `__main__` | 436 | 397 | 39 | 7 | 32 |
| the path alphabet, one character at a time (mine) | `_SEGMENT` | 95 | 58 | 37 | 1 | 36 |
| path and reader variants (mine) | spelling, reader | 39 | 27 | 12 | 3 | 9 |
| class-member removal over every other regex (mine) | spelling, reader's scheme | 372 | 101 | 271 | | note 1 |

The lead's measured block matches my runs:
- 78 sites with 76 killed;
- 61 of 61;
- "hand mutants: 68 in all, 50 killed, 4 survived, 14 not applicable";
- then 29 of 29.

**Equivalent survivors, with the argument.**
- `reader.py:170`, the descriptor and the root first, never fires.
  - The descriptor must equal a fixed dict, and six required root terms stand only on `./`. Any other entity second is refused `graph-form` anyway.
  - MEASURED (`corpus_verdicts.py`, round 2's corpus of 3,224 structural documents): verdicts identical to the shipped reader's.
- `reader.py:238`, a single-valued term given a list. `spelling.problem` refuses a list for every spelling, with the same name `spelling`. Corpus identical.
- `allow_nan=True` in `canonical.dumps` and `compact`. The reader refuses every NaN before it serialises. `1e999` is refused `spelling` either way, by the failed dump or by the bytes not being canonical.
- `spelling.py:92`, a size of 20 digits. Any 20-digit number exceeds 2^63 - 1 and fails the next test.
- `os.walk(followlinks=True)`. The link check on the parent's entries raises before any descent.
- Operator D's seven:
  - `reader.py:41`, `seen.add(k)` deleted. A repeated key then fails the canonical re-serialisation with the same name. Corpus identical.
  - `reader.py:129` with `2` to `1`. A one-entity graph is refused `graph-form` a few lines later.
  - `spelling.py:44`. `bits >> 62` gives the same result as `>> 63` for the two zeros.
  - `spelling.py:46` three times. The infinity branch never sees 0.
- Also equivalent: `/` added to the path alphabet (a segment has no `/`), `.`/`..` listed apart from the trailing-dot rule (`.` and `..` end in a dot), `lower()` for `casefold()` on ASCII, and `--fixtures` tested as `in args[:1]`.

**Real gaps.** R3-2 lists the 15 that matter. The rest of operator D's 32:
- `canonical.arrange` mutates its input when `e = dict(e)` goes (`canonical.py:52`).
- `arrange` sorts unknown list-valued keys when its guard changes (`:55`).
- The rational numerator's cap (`spelling.py:102`).
- The count boundary `held <= 0` (`checker.py:124`).
- The command line's argument tests at `:42`, `:52`, `:55`, `:57`, `:63` and `:65`.

One correction of my own: I first called `reader.py:129`'s `or` to `and` equivalent. The corpus showed it is not (18 crashes). It is R3-2 row 7.

### 4.3 Round 2's notes 1 to 13

| note | holds as the ledger says? | evidence |
|---|---|---|
| 1, registry limits | single quote and twin stage: yes. Mask: the instance only | MEASURED: deleting each of 12 stages is caught, as are a missing directory, the control made a plain stage, and a single-quoted guard. R3-3(a). |
| 2, the descriptor's case alias | yes | a File named `Ro-Crate-Metadata.json` is refused `graph-form`, "only by case". The lead's mutant (descriptor left out) is killed. |
| 3, invisible or ignored on disk | yes, stated in FORMAT.md | MEASURED on NTFS (`check\exp_stream.py`): an alternate stream on a listed file, a stream on `data/`, an empty directory and a hard link are each accepted, as stated. |
| 4, device names, 255 | yes | `COM0`, `LPT0`, `CONIN$`, `CONOUT$` are refused. 255 is accepted and 256 refused. A 255-character file name is accepted end to end on this host. Notes 5 and 6. |
| 5, the token pattern | yes for the snake-case family | MEASURED (`check\exp_privacy.py`): `token`, `access_token`, `refresh_token`, `id_token`, `auth_token`, `ibm_token`, `IBM_TOKEN`, `bearer_token` and more are caught after all 8 separators. camelCase (`accessToken`, `refreshToken`, `idToken`, `authToken`, `apiToken`) and `tokens` are not. |
| 6, NOTICE.md | partly; the ledger takes the use limits and the metric id, and neither takes nor declines the other two parts | Every clause NOTICE.md cites is in the IBM text the research agent extracted (MEASURED by search of its transcript: sections 5.1 to 5.4, 5.6 to 5.8 and 6.1.3, and the reverse-engineering and resale clause). The trademark sentence agrees with IBM's page, which lists Qiskit and IBM Quantum. The acknowledgement's second sentence is still the lead's wording; IBM's FAQ words it as the authors' views not reflecting IBM's policy or position. |
| 7, REFUSALS.md's graph-form row | one cause short | the root's `conformsTo` must be Process Run Crate 0.6 and this profile (`reader.py:185`); the row does not name it. |
| 8, "51 plants" | yes | the ledger's correction is accurate. |
| 9, where the `@id` and path rules are written | yes | CLAUDE.md points to `id_problem` and `path_problem`. |
| 10, the leap second | yes | the spelling's prose says it, and the examples refuse `:60`. |
| 11, a parcel's failing reader | yes | CLAUDE.md and FORMAT.md item 16 say so, and the planted tests show it. |
| 12, the study's status text | not taken, and stated | the approval paragraph covers it. |
| 13, a future `at` | yes | the custody docstring says it, and a test shows it. |

### 4.4 The changes beyond round 2's findings

- **`*` dropped from the path alphabet.**
  - It refuses `data/a*b.txt`, as claimed, in a planted test. Microsoft's naming page lists the asterisk as a reserved character.
  - It wrongly refuses only a POSIX file with `*` in its name. FORMAT.md item 11, the comment and the docstring all state that.
  - MEASURED: 2,000,000 random ids against a model written from FORMAT.md item 11 alone (`check\diff_path.py`): 0 disagreements, with 687,279 accepted and 1,312,721 refused.
- **`absolute()` needs a scheme of two characters or more, with no dot.**
  - It refuses `C:/x`, `notes.txt:hidden`, `a:x`, `7z:x` and `_x:y`, as claimed.
  - It wrongly refuses an IRI with a dotted or one-letter scheme (`iris.beep:`). That is negligible, and stated.
  - The stream sentence overreaches (R3-3b).
  - `spelling._IRI` still allows both, so the code has two meanings of "absolute IRI". No term uses that spelling, so it is not a defect.
- **A segment holds at most 255.** It refuses 256 and accepts 255, in a test. NTFS, ext4 and APFS hold 255. The total path is not bounded (note 6).
- **The descriptor's name counts in the case rule.** Planted, and the mutant that leaves it out is killed.

### 4.5 Anything else in the tree that is now false

- R3-1 to R3-4 are the ones I would restate. Section 5 has the points below the bar.
- The study has one new paragraph in section 17 ("A correction, after P0's second verifier") and one reworded sentence in section 15. I did not find two new paragraphs. The paragraph is accurate against the README's counts.
- CLAUDE.md, README.md, NOTICE.md and `docs/README.md` agree with the code and the files, apart from the points above.
- CLAUDE.md's line-ending claim holds. MEASURED: 8 files hold CR, all CRLF (the five instrument outputs and the three logs), none mixed.

### 4.6 The review copies

- **Copy against source.**
  - MEASURED (`check\review_check2.py`, my own line-level check, not the lead's regexes): all 15 copies are their sources after the stated changes, with 0 unexplained lines.
  - The per-file CRLF counts (291, 395, 226, 202, 270, 172, 131), the seven wrapped files, the home-path counts (1, 1, 0, 0, 1, 1, 0, 1, 1, 0, 0, 1) and the `<a home path>` counts (4, 1, 0) equal the READMEs'.
  - All 15 SHA-256 prefixes match.
  - Two changes are not stated: R3-4's final line feed, and the wrapper's `tool-use-id`.
- **Source against verifier.**
  - MEASURED (`check\sources_vs_transcripts.py`, `tx_compare.py`, `tx_round1.py`): 11 of the 12 study sources equal the last long message of a subagent transcript, once the transport's `&lt; &gt; &amp;` are undone. Each wrapper's task id names that transcript.
  - The twelfth, draft 4's, is the lead's transcription, as its README row says.
  - Round 1's interim report equals the first of that verifier's two long messages, and its final report equals the last.
- **Round 2.**
  - `round2.md` is its verifier's final message. MEASURED: the transcript's last assistant record (stop reason end_turn) is 34,805 characters. The staged source equals it with a final line feed added, and its SHA-256 begins `90e225a1`, as the P0 README says.
  - The copy differs from the source only by one redacted home path.

### 4.7 The usage-metric id

**UNKNOWN for the last step. IBM's public documentation cannot settle it.**

- **READ.**
  - IBM's Qiskit Runtime REST reference (Jobs, "Get job metrics") describes `usage.details[].metric.id` as the identifier of the metric definition from which the usage was calculated, a 36-character UUID. It does not say whether a definition is global, per plan, per instance or per account.
  - Its example carries a placeholder id that is version-4 shaped. Ours is version 5.
  - The "Workload usage" and "Monitor or cancel a job" pages hold no UUID and do not define "metric".
  - The qiskit-ibm-runtime issue 3431 quotes a real job's metrics from the same client versions, with `details` elided.
- **MEASURED, locally** (`check\metric_local.py`; the id was never printed and never sent).
  - The 65 records hold one distinct id, a version-5 UUID, in 65 usage details across ibm_fez, ibm_kingston and ibm_marrakesh.
  - It is absent, plain and without hyphens, from the three IBM Global Catalog pages an earlier probe saved (the service's children, its plan pricing, a search result).
  - It is not a uuid3 or uuid5 of any of the 466 strings in those pages, nor of any "a:b", "a/b" or "a.b" pair of 300 of them (270,000 pairs). I tried the DNS, URL, OID, X500 and nil namespaces and every UUID the pages hold.
- **BELIEVED.** A name-based id shared across devices and called a definition is more likely a billing-metric definition than an account or an instance id. Nothing public rules out a definition scoped to one instance.
- **What would settle it.** Read the same endpoint for one job of a second instance or plan, which is read-only and needs Logan's word, and compare. Or ask IBM. Until then NOTICE.md's "not established" is right.
- **Sent out.** No search or fetch contained the id or any part of it. I made three searches and eight fetches, all of public pages, with generic terms.

## 5. Notes (below the bar of a defect)

1. **The accepted side of the spellings is a sample.** Class-member removal over every regex in `spelling.py` and the scheme pattern in `reader.py`: 372 mutants, 101 killed, 271 survive. For example, `commit` has one accepted example (40 zeros), so 15 of its 16 hex digits survive. The digits of `time` and `date` survive, as do 48 of the 52 letters that may start a scheme. The 36 letters and digits of R3-2 row 11 are the path alphabet's share. Fix: one accepted example per spelling that uses every character of its class.
2. **Registry plants that go unseen** (outside its stated claims): the negative control's `MUST_SAY` removed; `-k` or `--deselect` added to a pytest stage; the lint cut to the package; the twin pointed at the control's plant.
3. **The privacy gate's docstring limit** ("caught only after one of the names listed") covers camelCase tokens, but the ledger's "its kin" reads wider.
4. **The acknowledgement's second sentence** in NOTICE.md and the README is the lead's wording (4.3, note 6). In NOTICE.md it sits outside the quotation marks, so it is not misattributed.
5. **FORMAT.md item 11** names `COM0`, `LPT0`, `CONIN$` and `CONOUT$` as names Windows reserves. Microsoft's naming page (updated 2025-04-11) lists COM1 to COM9, LPT1 to LPT9 and the superscript forms, not those four. The rule is a safe superset, but "reserves" overreaches for four names.
6. **Path length.** The rule bounds a segment (255) and not the whole path. Where Windows long paths are not enabled, MAX_PATH of 260 applies, so "the same file on every host" does not hold for a long path. This host has long paths on (a 421-character path worked).
7. **FORMAT.md item 7** says the header lives on the root. `qro:implementation` is a header term with domain `*`, so it can stand on any entity. The test in `test_canonical.py` says so; the item does not.
8. **`tests/docs/test_stage_registry.py:8`** says the tools include "every .py under docs/studies/qro0/". The code reads `check_*.py`. The others are covered by `test_the_study_instruments_are_run_or_stated`.
9. **The study's status line** still says nothing is built yet. It is dated to the approval, and the README says P0 is built.
10. **`verify/run.sh`'s `--list`** also gained a separating space (`%-10s%s` became `%-17s %s`). The header says only that the column is 17 wide.
11. **A user error on the custody command** (a missing log) exits 3, "the checker itself failed", and not 2. A missing crate directory is `file-missing`, exit 1. Neither is a wrong accept.
12. **Timing.** CLAUDE.md's "~15 s" is 15 s of stage time (17 s wall), and "~75 s" is 63 s of stage time (64 s wall). Both are fair approximations.
13. **A real FIFO or socket** still cannot be made on either host I have. The lead's plant patches `is_file`; the code path is read and plausible.
14. **The docs gate** reads the four root documents and `docs/*.md` only. 21 markdown files, 19 of them under `docs/studies/` and `docs/reviews/`, are outside it. I checked their relative links by hand: none is broken.
15. **My own scan** of the frozen tree for home-path, address, UUID and key shapes found only planted examples in `tests/tools/test_tools.py` and `tools/check_privacy.py`, and prose mentions of `~/.quantum-film` in the instruments and the reports.

## 6. What I did not do

- **No macOS run.** Linux is WSL2 with Python 3.10.12, not the required 3.12, on a case-insensitive Windows-mounted directory. I did not run `verify/run.sh` there. A case-sensitive host and the POSIX FIFO are BELIEVED, not measured.
- **No mutation of `controls/`, `tools/` or the tests.** I mutated `qro/` only. I probed `tools/check_privacy.py` and the registry gates by hand.
- **No IBM or Atlas contact; no qiskit import; nothing submitted.**
  - I did not open `~/.quantum-film`, any `.atlas` directory, or any key, token or CRN.
  - I read the subagent transcripts under the project's transcript directory (the verifiers' and the research agent's). I did so only to compare messages and to search IBM's extracted text. They are not credential files.
  - Every key-shaped string in my scripts is made up.
- **I did not re-read IBM's or Moth's terms myself.** IBM's terms pages are script-rendered and my fetch returned nothing. NOTICE.md is checked against the research agent's extracted text and its report.
- **No `rocrate-validator` or JSON-LD processor,** and no performance test on a large crate.
- **No review of P1 to P5,** which do not exist yet.
- **Slips of mine.**
  - My first listing of the frozen tree printed the file names under `records/`, which contain IBM job ids. They are in the tree already, and I masked every later print.
  - I wrote three small listing files to the shell's `/tmp`, outside my directory, and deleted them.
  - Several scripts run with `python -I` ignored `PYTHONDONTWRITEBYTECODE` and left `.pyc` files in my own pristine copy. I deleted them, and `frozen\` never held one.
  - My first review check used a character-level diff that fragmented each redacted path. I replaced it with a line-level check.
  - My first reading of the registry plants was polluted by the lead's own plant tests failing on my edited runner. I reran with only the gate tests selected.
  - One demonstration (the custody chain) first built a log that was not broken. I fixed it and reran.
  - I first called `reader.py:129`'s `or` to `and` equivalent. The corpus corrected me.
- **No one was contacted, and no banner accepted.**

A scoped re-check after the fixes should cover R3-1 to R3-4. It should also re-run operator D, the command-line set, the path set and the class-removal set. I will pick my own faults again.
