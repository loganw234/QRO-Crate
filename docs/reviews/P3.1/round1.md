# P3.1 round 1 verifier report

**Verdict: NOT READY, on one finding (D1).** It is a statement sentence that says more than its condition shows, in the same shape as limit 18. P3.1 does not list it as a limit. I found no wrong verdict, no skipped or misordered refusal, and no unsafe `make`. If you rule D1 as you ruled limit 18, I have no other blocker.

Everything below is MEASURED in my sandbox copy unless it says READ or BELIEVED. My notes are in SCRATCH\verifier-P31-r1\check\notes.md.

## The freeze and the change
- **The freeze holds.** SHA256SUMS.txt begins `953637b3f79642e8`, and all 556 files match.
- **The change is as the lead measured it.** Against base 0813f8c, 34 files are added and only docs/README.md is changed, by two index lines. No file of P0's, P1's or P2's moved.
- **The new files are clean.** All 34 are ASCII with LF and a final newline. I found no 20-character job-id shape in them, or in the builder's scratch notes and scripts.
- **The runner passed.** The full runner in my copy, run `20261108-132548-37948-e7e209b` (commit e7e209b in my sandbox repository), gave passed 26, failed 0, skipped 4. The four skips are lint-kit, p5, p5-kit and p5-crates, the only ones allowed.
  - `p3` took 146 s and `p3-crates` 136 s, on a loaded machine.
  - The controls' run gave 22 of 22 built controls as section 11 says, and 8 pending.
- **I did not run the quick budget.** I only listed its stages.

## Defect

**D1. Prose and code: `compile-unheld` is said where the compile is `unexposed`.**
- **The fault.** `statements` in qro/p3_verdicts.py says `compile-unheld` when `causes["compile"] == "unexposed"` or when the compile DIFFERS and is not held. The sentence is "not isolated from the pipeline: the compile DIFFERS and is not held". Where no member Pub has a manifest circuit, nothing shows that the compile differs. The record's cause status says `unexposed`, so the record itself is honest.
- **The evidence.** In READ code, the unexposed branch in `statements`. In MEASURED terms, `test_its_twin_the_same_declared_a_rehearsal_is_computed_and_says_so` asserts `compile: unexposed` together with `compile-unheld` and `submitted-differs`, on Atlas against IBM. The design's table groups unexposed under "DIFFERS, not held", and the page's limit 18 names only `submitted-differs`.
- **What it needs.** A ruling like limit 18's, and a line in the page's stated limits. This is a statement-level overclaim, and the conclusion (not isolated) holds either way.

## What I worked out myself, which matched P3
I wrote an oracle (work\oracle.py in my sandbox) from `p1_graph.Index`, `p2_measures.pub_values` and `p2_interval` alone, with my own M. It matched P3 on every interval, difference, drift, strong form and means.
- **Builder crates.**
  - Five measures with 3 and 2 members: M = 25, as I counted it.
  - Runs with members whose shots in scope are 0 (one pooled, one a single member): vacuous interval, still counted in M.
  - Epsilon set exactly at L, at U, and at plus and minus 2^-60 of each, on three law measures: L equal to epsilon is not `differ`, and U equal to epsilon is `agree`.
- **v0, from the real crates built with P1's adapter.** All five measures of three device pairs match the oracle.

  | Pair | M |
  |---|---|
  | kingston and fez | 70 |
  | kingston and marrakesh | 70 |
  | fez and marrakesh | 76 |

- **Statements.** `isolated-pipeline` is reached and said (strong form 0.875 against epsilon 1/100). It is not said for blocked times, commit unknown or differing, a compile that differs and is withheld, or a varied question. `device-alone` and `device-and-time` follow the alternation.
- **Refusals.**
  - Trivial by job id alone and by commitment alone, and trivial before kind and before question.
  - `question-differs` before `role-missing`.
  - A partial `role-missing` goes on, and a whole one is refused.
  - `kind-not-qpu` comes before the covered-readout `step-unbuilt`.
  - A covered readout is refused `step-unbuilt` at "&lt;measure&gt;: the readout bound", and the same controls on only one run give UNMEASURED.
  - A tie with the job before gives UNMEASURED.
- **Late.** The plan's digest as a whole token gives "pre-registered". The digest followed by a hex digit, in upper case, or preceded by a `0` gives `selector-late`.
- **The record.** A tampered `means`, a dropped statement, a flipped `late`, and a CRLF spelling of the record are each refused `comparison-generated` at the first difference. An extra file is refused `file-unlisted`, and a changed pre-registration `file-digest`. A refused crate is named at "crate 2".
- **The command.**
  - **Acceptance:** `compare` is accepted, in either order of the crates.
  - **The comparison's own directory** given again as a crate is exit 2, spelt as given, with a trailing slash, in upper case, through `..` and `.`, as the 8.3 short name, and as a junction.
  - **Missing or wrong arguments** give exit 2: a named crate not given, a comparison crate named in the pool (refused `question-differs`), a crate with no comparison. A pool that names a comparison crate also gives `question-differs`.
  - **A closed stdout** gives exit 3 for `compare` and for `make`; a closed pipe gives exit 3. I never saw 120.
- **`make`.**
  - It refuses as misuse, and writes nothing, an out that is not empty, is a file, lies in or around a crate, lies in the tree, or is a junction into either.
  - A failed make leaves nothing, and keeps a parent that was already there.
  - An out that is a junction to an empty directory works.
- **The declaration reader.** 6,000 byte-level mutations of a good declaration gave no escaping exception. 145 were accepted, each in its one canonical spelling.
- **The controls** through `python -m controls.plant` are as the page says: `self-compare` and `resealed-compare` are refused `comparison-trivial` by the same job id, `shared-control` is accepted, `joint-omission` is refused `comparison-generated` at line 48 column 13, and `readout-unbounded` is accepted and pending.
- **P4's walk of accepted plants** still skips a `Compared`, as `test_p4s_walk_of_accepted_plants_still_skips_a_tuple_a_compared_among_them` holds, so P4 does not examine P3's accepted plants (READ).

## The nine readings and limit 18
- **The nine readings are sound.** Each refuses or says UNMEASURED where the design was silent, and none passes what it should refuse. I attacked readings 1, 2, 3, 6, 7 and 8 directly.
- **Limit 18 is true of the code.**
- **The page's counts are true.** Every case count the page states matches the collected tests, and 46×6×2×4×4 = 8,832.

## Notes (below the bar)

**Test reach where the code is right.** I ran 23 hand mutants through my own runner, which copies the tree and deletes nothing. 13 were killed by their target. Six survived the whole of tests/p3, and three were equivalent.
- **Survivors.**
  - `what was submitted` ignoring `decode`, `route`, `program` or `kind`. The builder holds those four constant, so only options and shots are exercised, which is what the page says.
  - The readout coverage loop using only the first qubit. The builder's controls always cover qubits 0 and 1 together.
  - The `decode` factor of `unseen` ignoring bit order.
- **Equivalent.**
  - `exposed` without the manifest test.
  - The directory-conflict swallow in `_Made.directory`.
  - Dropping `_inside(c, out)`, because a non-empty out is refused anyway.

**Unpinned imports.**
- `_held_manifests` in qro/p3_runs.py re-implements P2's public `p2_measures.manifest_of` (one File named manifest.json) instead of importing it. Its docstring says "as step 7 reads it". No test pins the two together.
- `manifest.circuits()` is called but not in the independence test's pins. The pin test sees only attributes taken on a module, so the page's "each name and signature P3 calls ... is pinned" is slightly broad.

**Other.**
- Mixed commits (one `unknown`, others differing) say only `commit-unknown`. The cause status is single-valued, and the design is silent on precedence.
- An out that is a dangling junction gives exit 3 ("make itself failed", FileExistsError) rather than misuse. Nothing is written. It is host-specific.
- If stdout is closed, `make` has already written a valid crate when it exits 3.
- The `question` cause is EQUAL when both runs' logical circuits are `unexposed`, and `unseen` then lists `question` as shared. `isolated` still needs `submitted` EQUAL, so no statement overclaims.
- No P3 test makes a junction, so none can be left in pytest's temporary folders (READ, grep). The junction and 8.3 spellings of the comparison's own directory are not in the five-spelling test. My MEASURED runs show they are refused.
- P3 tests spawn no windowless processes (BELIEVED, no use of the flags found).
- The `p3_runs` structure test poisons only two count readers, `parse_raw` and `pub_counts`.

## What I did not do
- I did not run the quick budget or the lead's merge run, and I did not wait for the lead's run.
- I did not check the builder's slips beyond the ledger text. That a 12-byte file was made and removed, and the other reported slips, is BELIEVED from the ledger.
- I did not run P3's test_p3_cli.py or the bash-using tests apart from the runner's own run, and I did not run my mutants on the bash-based tests.
- I did not read, edit or run anything in frozen\, the worktrees, the lead's clones or the real repository, beyond read-only `git show` and `ls-tree` on base 0813f8c.
- I did not touch IBM, Atlas or any key.
- I removed every junction I made, live, in my sandbox directory, and left none.
