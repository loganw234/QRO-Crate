# P5.1 verifier, round 1: verdict NOT READY

One defect in what the code does. It is in `preflight_ok`, the shipped S7(c) acceptor. A pre-flight record dated in the future passes the "under 24 hours old" rule, forever. The real route is unreachable in P5.1, so nothing could be submitted today. P5.2 inherits the acceptor as it stands.

My full runner was still going when I stopped. It had passed: lint, lint-kit, docs, check-docs, vocabulary, tool-tests, vocab-tests, format, custody, p1, p2, p4, p5 (307 s), p1-crates and p2-crates. p3 and p3-crates skipped by name, as allowed. p5-kit, p5-crates, privacy, privacy-controls and the rest had not finished. I cannot vouch for those stages. I judged them by my own attacks and by the lead's run.

## Defects

### 1. S7(c) accepts a future-dated pre-flight record (code)
READ and MEASURED, with a script run on `qro_kit/submit.py` through sbx.sh in the kit's interpreter.
- `preflight_ok` tests only `now - at &gt;= 24h`. A record whose `at` is in 2099 and whose `holds` is `"holds"` returns `(True, '')`.
- A future-dated holding record also becomes "the newest" and hides a real, older failing record. Measured: an old failing record plus a future-dated holding one returned `(True, '')`.
- The rule is "a pre-flight record under 24 hours old that holds". A record dated ahead of now is not that.
- Fix: refuse `at &gt; now`, or require `0 &lt;= now - at &lt; 24h`.

## Notes

Everything below is below the bar.

### Tests and gates
- **GU7 test gap (test gap; the code is right).** I mutated GU7's "a status job has no metrics or verdict" check down to "no records". The generator tests did not catch it: `test_gu7_a_job_with_a_status_file_and_a_record_is_refused` always has records present. I stopped the harness before the six-directory fallback, so I do not know whether any other test catches it. Mutants 0 to 2 were killed (GU6 pair roles, GU3 job-id uniqueness, GU7 raw-xor-status). I did not run the other 13 of my 16 mutants.
- **`.pyd`/`.pyc` hole in the vendoring loader (gate; the code is right).** `_qf.problems()` scans only `*.py` for unlisted files. A committed `.pyd` or sourceless `.pyc` in `_vendor/quantum_film` would load ahead of the source. `test_nothing_else_is_vendored` does catch it, because it uses `rglob("*")`. The loader does not.
- **Sampler `ast` test (test reach).** `test_a_sampler_is_run_only_in_submit_send` exempts receivers named `runner` and `q.runner` by name.

### The kit
- **Stale `.pyc` in `__pycache__` (code; stated in design item 14).** D2 skips `__pycache__` by name, so a stale or planted `.pyc` passes `kit-dirty`. The kit only sets `sys.dont_write_bytecode`.
- **`check_usage` crash on infinity.** An infinite `usage_remaining_seconds` raises `OverflowError`, which becomes exit 3 instead of a `spend-usage` refusal. Numeric strings like `"600"` are also accepted. Unreachable in P5.1.
- **Misleading message on an undriven unit.** `crate` on a frozen unit that was never driven is refused `spelling at #unit qro:unitJobs: a list of one value or more`. It is a refusal by exit 1, and the out is removed, but the message is misleading.
- **A failed git push in `freeze` exits 2.** That code means misuse, not a kit failure.

### Intake
- **Intake record fields.** `--record` always writes `tool: unknown` and `unit_commit: unknown`.
- **Divisor not visible at intake.** A divisor-128 unit is `ACCEPTED ... unit` with nothing saying it is scaled. Only `recipe_sha256` differs, so P3.2 must compare it.
- **Film-before-control order.** A film job submitted before its pass's control job is accepted with no `KEPT` line. That matches the design, because the gate is the kit's.
- **Free-text `UNIT.json` terms.** An extra key, `kit_tag` `"qro-kit-v1"`, a contributor with U+0663, and CRLF in `UNIT.json` all regenerate and are accepted. These terms are REPORTED text by the vocabulary.
- **Float cap.** GU1 accepts `max_execution_time` `60.0` for `60`; `check_cap` at drive time would refuse it.

### Prose
- **docs/P5.md contradicts itself on the full-unit time.** It says "about 80 minutes here, MEASURED below". Below, the 80-minute figure is BELIEVED (4,870 s), and the one measurement is 7,982.9 s.
- **docs/P5.md item 16 and crate refusal.** It says a control job that stops the unit leaves it "contributed incomplete". A control PUB that fails would be refused `known-answer` at crate and intake instead. BELIEVED, not run.
- **Full-shot unit figures.** The log (`full1.log`) agrees with the report: 7,982.9 s, 197 files, 16,201,153 bytes, ACCEPTED. The crate itself is gone from the builder's sandbox, so I could not re-check it.
- **Other docs.** NOTICE.md and CLAUDE.md match the code. The 114 + 7 mutant count in docs/P5.md differs from the report's 132, which includes the gate's 11.

## What held (MEASURED unless marked)

- **Freeze.** SHA256SUMS matches (587 files; hash begins `da27cbfe`).
- **Vendored bytes.**
  - All 22 modules, the licence and the circuit equal moth-quantum at 3a73823. `VENDORED.sha256` names exactly those 24 files.
  - A changed byte, an extra `.txt` or `.py`, a removed file, and a trailing newline each fail `tests/p5/test_p5_vendored.py`.
  - A byte edit with a matching list line fails the pinned 194,424 total, and `tests/p5crates` fails it against moth.
- **Privacy gate `KNOWN_FILES`.** I attacked it on 14 repos and nothing passed that should fail. I did not run the gate's own plants (privacy-controls); the runner never reached that stage.
  - Known bytes alone: 0 bad, 2 known.
  - Fail: a second alternative appended, one byte appended, a UTF-16 or UTF-8-BOM version, upper-case, a `x/` prefix, a second path with the same bytes, and a junction to other bytes.
  - Staged and disk versions that differ fail on whichever side differs.
  - A known file committed and then changed leaves its old blob failing in history, as stated.
- **`kit-dirty`.** Thirty scenarios through `tree_state`.
  - Refused: edited, assume-unchanged, skip-worktree, untracked, untracked by ignore or `info/exclude`, a junction, `git replace`, a clean filter, fsmonitor, CRLF swap, a deleted file, an untagged HEAD, a stale tag, and bad tag names including U+FF11 and U+0661 digits.
  - The CLI refuses `freeze`, `drive` and `crate` on a dirty tree and on an untagged tree.
- **Real route.**
  - `--route real` is always refused: no confirm, wrong confirm, no pre-flight, and a forged holding pre-flight (which ends at "no connection to IBM").
  - `freeze --route real` is refused `route-unsafe`.
  - There was no `-submitting.json` and no run directory afterwards.
  - READ: the only `SamplerV2` and `.run(` are in `submit.py`. The vendored `account.py` takes its service class as an argument and the kit never calls `connect`. The constants are 270 s, 15 s / 60 s and the tag pattern.
- **Removals.** `remove_listed_tree` and `Made.clear` left every junction target intact in four cases, and left foreign files alone when a directory was swapped under them. A failed `freeze` left no WORK.
- **CLI exits and S1.**
  - Misuse exits 2; refusals exit 1 with one line.
  - A closed stdout exits 3, never 120.
  - Re-driving a driven unit is refused `once-only` with the directory byte-identical.
- **Local unit end to end (divisor 128, 197 files).**
  - Freeze took 20 s, drive 6.5 min and crate 19 s. The checker and intake accepted it.
  - My tampers on that crate:
    - known answer: refused by the checker and by intake;
    - complement alone: accepted by the checker, refused at intake;
    - incomplete: `KEPT`;
    - blocks: `KEPT`;
    - raw byte edited: `raw-digest`;
    - extra root file: `file-unlisted`.
  - GU1 to GU10 refused my own faults with the expected letters. Mixed-role GU9 is tested by the builder; I did not re-run it.
- **Controls.** `controls.run` came out 22 of 22 built controls as section 11 says. `kit-dirty` is refused by name, and `unit-known-answer` is refused `known-answer`. The two `states` rows are covered by `controls.run`, which printed `states` for both. `controls.plant` prints only `ACCEPTED` for them.
- **Changes against base.** Exactly 60 added and 6 changed, all six granted. The stub change in `tests/controls/test_control_registry.py` is the `**kw` edit only. The 60 added files are LF and ASCII apart from the one U+0663 in `tests/p5/test_p5_recipe.py`. I found no job-id-shaped strings.

## What I did not do

- I did not finish the runner. I did not see p5-kit, p5-crates, privacy or privacy-controls pass, and I did not compare the `garbage-*` junction folders (41 at the start).
- I did not build a full-shot unit, and the builder's full crate no longer exists.
- I did not run a mutant of `submit.py`, `freeze`, `drive` or `crate`, or the gate's own plants.
- I ran one `git tag -d` and one `git tag` on my own sandbox copy, `tree3`, without the launcher. It touched only my directory.

The report was not written to the check directory; this message is the report.
