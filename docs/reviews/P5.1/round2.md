# P5.1 round 2: verifier's report

## Verdict: NOT READY

The only defect is in prose: docs/P5.md promises a round 2 mutant tally and doesn't hold one. D1 and all six rulings hold in the code. The fix is one passage in docs/P5.md.

**The freeze** (MEASURED, `sha256sum -c` and `diff -rq` against round 1's packet):
- The packet's SHA256SUMS.txt begins `2d39ddf259ef97d2`.
- Every file in tree\ matches it.
- The tree differs from round 1's packet in exactly the 12 named files and no others.

**My full runner,** on a git-initialised copy of the packet in my sandbox, through sbx-mid.sh:
- Run id `20261108-233732-63535-c589aab`: 28 passed, 0 failed, 2 skipped. p3 and p3-crates skipped by name, which is all that may skip on this base.
- p5 took 285 s and p5-kit 646 s. That puts the builder's 788 s for p5 down to load, not new cost. I did not time round 1's tests/p5 on the same machine, so the comparison is against its 324 s figure.
- The lead's own run of round 2 had not reported to me when I finished.

## Defect

**Prose, docs/P5.md.** Line 241 says "(round 2 adds its own, below)". Nothing below gives round 2's mutant tally, and "round 2" appears nowhere else on the page (`grep -in "round 2"`). The builder's 20 of 20 is only in its ledger.
- Ruling 7 asked for "the mutant tally" on the page, and a claim in the tree that is false is on the bar.
- Fix: add the round 2 line (20 round 2 mutants, all killed, the equivalent D1 one noted), or drop "below".
- This is not a code defect. Only the docs gate would have caught it, and the docs gate passes.

## What holds (code)

**D1, `preflight_ok`.** I ran 30 scenarios through the function (MEASURED, check/d1.py):
- **Window edges:**
  - Taken: a record at exactly now, and one at 23:59:59 old.
  - Refused: 1 s ahead, exactly 24 h old, 24 h and 1 s old, a record dated 2099 or 9999.
- **Mixed records:**
  - Refused as "does not hold": an older failing record beside a 2099 holding one, or one an hour ahead.
  - Taken: an older holding record beside an hour-ahead failing one, because the ahead record is ignored.
  - A newer failing record beats an older holding one, and the reverse.
- **Unusable records, all refused:**
  - Another unit's digest, with or without an own failing record.
  - No `at`, an unparseable one, a null or integer one.
  - Time zones `+00:00` and `-07:00`.
  - A leap second (`23:59:60Z`).
  - `holds` as a bool or `"HOLDS"`.
  - A top-level list, and bad JSON.
- **Garbage beside a good record:** a good holding record is still taken.
- **Mutants:** I ran 10 mutants of the D1 code against tests/p5/test_p5_spend.py. Nine are killed. Dropping the lower bound alone survives, and it is equivalent: once records ahead of now are skipped, `now - at` can't be negative.

**The six.**
- **GU7:** a status job with metrics, with a verdict, with records, and every combination of them, are refused. A bare status job passes GU7. The check is unchanged from round 1 and the test is new. Four of the six GU7 mutants I ran are killed, including a pass of metrics-only and of verdict-only.
- **Vendoring loader:**
  - **Plants:** I planted 22 unlisted names, and every one is refused. They include `.pyd`, `.so`, `.pyc`, `.dll`, `.pth`, `.pyi`, no extension, upper-case, a `__pycache__` file and a stream name.
  - **Replacements:** a directory in place of a listed file, a case change of a listed name, a junction to a directory holding a file, and a junction replacing `ibm/`.
  - **Mutants:** the four loader mutants I ran are killed.
  - **Left alone:** an empty directory is clean.
  - **Cleanup:** no junction was left behind.
- **Git failure in `freeze`:**
  - A real failing push (git's sh crashed at low integrity) gives exit 3, `GitFailed`, one FAILED line, and no `--out` left behind.
  - Git missing from PATH also gives exit 3. A broken global git config gives the `kit-dirty` refusal, exit 1, as before.
  - I did not make a push fail at normal integrity, so no controlled push failure was run.
- **GU1 cap:**
  - `60.0`, `"60"`, `true`, `null`, `60.5` and `[60]` are refused on three jobs of two devices.
  - `-1` and a huge integer are refused by the job-table check, and the same integer passes.
  - One mutant of the cap check survives: `isinstance` in place of `type is int`. It is equivalent, because a bool never equals a cap of 15 or 60 and the job-table check refuses it.
- **Intake line:**
  - Divisors 1 and the qpu twin give `ACCEPTED &lt;digest&gt; unit`.
  - Divisors 2, 4 and 128 give `… unit scaled by shots divisor N`. This includes round 1's crate.
  - A recipe digest matching no divisor is refused (`file-digest`, and GU2 on regeneration).
  - All four intake mutants I ran are killed.

**`qro/p5_unit.py`** differs from round 1's by `shots_divisor`, `Intake.divisor` and the `lines()` change only (READ, `diff -u`).

**Moved by round 2:** the real route stays refused, every `--out` was removed after a failure, the exits are unchanged, and the control crates still pass. The files changed are P5's own. I found no vendored byte changed, no weakened guard, and no junction left in my directory.

## Notes (below the bar)

- **Code, tie-break:** two records of the same second, one holding and one failing, are decided by file-name order. `holding` first gives True. P5.2's records are named by UTC second, so this is likely unreachable. A failing record winning the tie would be safer.
- **Gate:** `_qf.problems()` now refuses any file under `quantum_film/`, including a `__pycache__` `.pyc`, while `kit-dirty` ignores `__pycache__` by name. A stranger whose other tooling leaves a `.pyc` there gets a clean refusal naming it. It never passes bad code. The runner stages passed, so the kit writes none. This touches the `__pycache__` item already recorded for P5.2.
- **Prose:** none beyond the defect. Item 16 matches `drive.py` (`CODE_NOT_HOLDING = 3`). The 7,982.9 s and 1.6 times figures agree with the page's 4,870 s.

## What I did not do

- I did not build a full-shot unit.
- I did not compare p5's time on round 1's packet in the same session.
- I did not make a controlled git push failure at normal integrity.
- I did not receive the lead's own run result.
- I connected to nothing and submitted nothing.

My short report is at `<scratch>\verifier-P51-r2\check\round2-report.md`. My scripts and logs are in `<home>AppData\LocalLow\qro-sbx\p51-r2\check\`.
