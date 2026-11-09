# P5.1 round 3: READY

No defects. The passage is on the page where the item says it is, and every claim in it held under my runs.

## What I measured

- **The freeze (MEASURED).**
  - The SHA256SUMS.txt hash begins `ffc06496c0b22af4`, as stated.
  - Every file in the tree matches its line in SHA256SUMS.txt.
  - `diff -rq` against round 2's packet names one file, docs/P5.md.
  - docs/P5.md's diff has two hunks:
    - The item "Mutants (round 1)" loses "(round 2 adds its own, below)".
    - The item "Mutants (round 2)" is added.
  - Nothing else in docs/P5.md moved.
  - The file is ASCII, with no CR byte.
- **The count (MEASURED).** mutants_r2.py holds 20 entries, which split as the passage says:
  - 6 of D1
  - 4 of GU7
  - 2 of the loader
  - 2 of `freeze`'s failed git
  - 2 of GU1's cap type
  - 4 of the scaled unit's line at intake
  - The total, 152, is round 1's 132 plus 20.
- **The baseline (MEASURED, sbx.sh).** I ran each of the six target selections on the unmutated copy first. All passed: 22, 9, 21, 13, 1 and 7 tests. So a target failing would be a real kill.
- **The 20 mutants (MEASURED).** I re-ran them with `bash sbx.sh python -I hm_p5.py tree work-r3 mutants_r2.py`, through sbx.sh alone. The tally was `{'targeted': 20, 'pytest': 0, 'SURVIVED': 0, 'N/A': 0} of 20`. All 20 were killed by their own target tests.
- **The equivalent D1 mutant (MEASURED).**
  - I ran the lower-bound-only mutant against test_p5_spend.py. It survives the spend tests, which is what "equivalent" predicts.
  - I read `preflight_ok` (READ, qro_kit/submit.py lines 112 to 138). A record dated after `now` is skipped before it reaches `found`, so `now - at` is never negative where the window is tested.
  - The passage's reason, "no record is then dated ahead of now", is true.
  - The harness's wide fallback then printed "KILLED (tests/p5, not by its target)". That was not the mutant. The harness restores the file after each mutant, and I reran tests/p5 on the restored, unmutated copy. It failed the same way, on `test_d1_a_clean_filter_that_makes_git_status_clean_over_changed_bytes_is_dirty` (git's clean filter runs through sh, which cannot run at low integrity). The tally of 20 does not count this mutant.
- **The ledger (READ).** The entry of `2026-11-09T06:00:00Z` says 20 of 20 killed, three survived the first run (the skip moved a day, GU7's records dropped, the loader's link skip), each killed after a test was added, and the lower-bound mutant equivalent and not in the list. The page says the same. Round 2's report says the same of the lower-bound mutant.
- **The quick budget (MEASURED).** I ran it with `bash sbx-mid.sh bash verify/run.sh --budget quick`, with the three variables set, in a git-initialised copy committed as b09b465. Run id `20261109-012829-14835-b09b465`: 20 passed, 0 failed, 1 skipped by name, which is p3. That includes the docs stage (ok, 211 s) and check-docs.

## Defects

None.

## Notes

- **Prose.** The passage says the three survivors were "killed after a test was added for it", and the ledger agrees. I did not re-run the first-run survival, because the packet holds only the final tests. It follows from the ledger and I did not disconfirm it (BELIEVED).
- **Gate.** The hm_p5 harness's wide fallback counts any rc 1 as a kill, so an environment failure at low integrity reads as a kill. It misled me once here, and a survivor would be mistaken for a kill the same way. A fix is for the harness to run the fallback on the baseline first. Not a defect of P5.1.
- Rounds 1 and 2's notes are left as ruled.

## What I did not do

- I did not run the full runner. The lead's merge does.
- I did not run a full-shot unit.
- I did not connect to any network or to IBM.
- I did not touch the key, any credential file or the ledger.
- I did not edit anything outside my directory, `<home>AppData\LocalLow\qro-sbx\p51-r3\`. Nothing of mine is left running. No junction was made.

A short stub of this report is at `<scratch>\verifier-P51-r3\check\round3-report.md`.
