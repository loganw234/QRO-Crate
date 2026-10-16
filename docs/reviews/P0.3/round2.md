# P0.3 verifier, round 2: READY

On the full bar I found no defect. The code, the gates and the table are right, and I found no false claim I would call a defect. I list gate reach, test reach and prose slips as notes below, and I say for each why it does not block.

## Freeze and base
- **Freeze (MEASURED).** `SHA256SUMS.txt` begins `384581d0f3a7bb46`. `sha256sum -c` gives 253 of 253 OK, with the same file set. I re-checked at the end and nothing in `frozen\` changed.
- **The moved base (MEASURED).** I copied P0.2's round-4 tree and ran `p03_edits.py`, `p03b_edits.py`, `gen_vocabulary.py --write`, `write_golden.py` and `p03c_records.py` on the copy. The result is byte-identical to the frozen tree, except for a `tools/__pycache__` the scripts made. P0.2's round-4 hunks (`pyproject.toml`, `check_privacy.py`, its tests, and parametrized git-env tests in the same registry file) touch none of P0.3's anchors or meanings.
- **Tests (MEASURED).** P0.2 round 4 has 966 tests and P0.3 has 984. By test id, two were renamed and 18 added, and none were dropped.

## Runs (MEASURED)
- **Full runner** (`QRO_MOTH_ROOT=… bash verify/run.sh`, git-init'd with no commit): 17 passed, 7 skipped by name, 0 failed, in 159 s. P0.2's verifier was running beside me, so the time is noisy.
  - Test counts: docs 136, tool-tests 106, vocab-tests 11, format 676, custody 23, control-tests 32.
  - The other ledger figures all reproduce: controls 9 of 9 with 21 pending, study plants 68 and 6, privacy 253 files and 0 commit messages, privacy controls 37 of 37, instruments 5 of 5.
  - check-docs reads 10 documents, 35 other markdown files and 35 source files. The twin is `21fafec5…`.
- **Quick budget:** 14 passed and 4 skipped by name, in 70 s.
- **Stand-in parcels** (round 1's P4 tool, `register_p1`, `register_p2`, `tests/p1`, `p1crates`, `p2`, `p2crates`, `p4`, `p4shacl`, with both variables set): all 24 stages passed in 140 s.
  - The guards behave as CLAUDE.md says with neither variable, with moth only, and with the engine only under `--require-all`.
  - I used the engine only for its fingerprint and a stand-in test that ran `-I -c "print(1)"`.

## Round 1's defect and notes
- **D1 (study "four" to "three"):** fixed. `QRO-0.md` lines 1541-1543 say "three". A grep finds no other count of the checks, and both study gates accept.
- **Naming rule, term and type of one name:** holds. In a 13-case battery of `sanity()` input, `qro:Pub` as both is refused as "both a term and a type", and case twins are refused.
- **`need_env` rule:** holds for misspellings only. Truncated, suffix, case and transposed names are all caught. Deleting a guard or pointing it at another variable is not caught (see note 1).
- **Engine in the fingerprint:** holds.
  - The line is the path plus `804204a1b1386367`.
  - On a committed scratch copy, `--resume` with the same engine continued. Unset or another interpreter was refused.
- **Reader's order:** pinned at two boundaries, not at a third (see note 3).
- **Round 1's prose notes** (study section 10, FORMAT.md items 19 and 21, the `graph-form` row, future tense, the 33 s figure, the registry docstring) are all taken (READ). The local dates are fixed except for one leftover (see note 5).

## Code and gate checks that found nothing
- **Table against the designs (MEASURED).**
  - Round 1's `atk_table.py`, which parses the ledger's own tables, reports 15 plus 19 new rows and 9 changed rows with 0 differences in key, kind, spelling, many, absent, step, domain and owner.
  - I cross-read the six word sets and the nine types against P1's item 7 and P2's item 10 myself. The two widened refusal meanings equal P2's text exactly. The `context` row matches D10.
- **The reader's profile rule (MEASURED).**
  - 200,000 random graphs through `_profiles` against an oracle I wrote from D1 and D10 gave 0 differences and 0 crashes.
  - 100,000 byte and structure edits of the twin through `reader.read` gave 0 crashes. In 60,000 of those I checked that every accepted graph holds exactly the two table entities and no other `Profile`-typed one: 0 wrong accepts.
  - As a process, hostile versions (lone surrogate, NUL, escape, 200,000 digits, nested list) give exit 1 and one ASCII REFUSED line.
- **Round 1's P1-design graph and P2 shape checks, re-run on this tree:** the same results as round 1 (MEASURED). The one expectation that changed is `version` on a `SoftwareApplication`, now `graph-form`.
- **Goldens:** the twin re-derives with `json` and `hashlib` alone.
- **`check_docs`:** it fails a page with no index line and an index line with no page, as CLAUDE.md says.
- **The controls:** all 30 fault texts equal the study's section 11 rows.
- **The lead's mutants (reproduced):**
  - `m_p03.py`: 23 killed by the targeted test, 1 by the wider suite, 2 not applicable because the round-1 fix moved their anchors.
  - `m_p03_r1.py`: 8 of 8 killed.
- **My own mutants:** 32 in two batches, 21 killed and 11 survived. The survivors are in the notes below.

## Notes
**Gate**
1. **`need_env` rule.** Its docstring and the ledger say it holds the runner "reads" the variable. It accepts any `$NAME` outside `need_env` lines, comments included.
   - MEASURED: with both `QRO_SHACL_PYTHON` reads in `shacl_engine` commented out and their text left, `tests/docs` still gives 136 passed.
   - MEASURED: deleting `need_env QRO_MOTH_ROOT` before p1-crates, and pointing p1-crates at `QRO_SHACL_PYTHON`, both survive the whole suite. These are the cases round 1's note 3 named, and the ledger's "Not taken" does not list them.
   - Why it does not block: the rule's stated purpose, a misspelt name, is met. Fix: drop comment lines from `elsewhere`, and optionally tie each `need_env` to its stage.
2. **Fingerprint line.** Removing the engine's `echo` line, or its `-I`, survives all tests. The ledger says the line is held by no test, and its behaviour is right.

**Test reach, code right**

3. **Reader order, and extras.**
   - Moving `_profiles` between the `mentions` check and the reference check survives everything, though the reader's docstring lists profiles before mentions.
   - An extra `Profile` entity typed other than exactly `["CreativeWork","Profile"]` is not pinned.
   - The shipped code refuses both (MEASURED).
4. **Incidental kills.** Two of the lead's "targeted" kills of runner mutants, mine numbered 13 and 18, come only from tests that search for the literal text the mutant deleted or changed. The kill is real, but it is not a rule.

**Prose and other**

5. **Dates.** `VALIDATION.md:1858` says P2's and P4's designs were "approved 2026-10-16". `vocabulary.py:254`, `run.sh:342` and `:350`, and the study say 2026-10-15, which the second entry says is the convention. The first entry may have been left as the first verifier read it.
6. **`qro:lawCircuit` meaning.** `vocabulary.py:258` drops P2's "and its coherences", so the generated page understates what step 6 holds. It is an abridgement, not a contradiction. `qro:line` ("a job" for "the job") and `qro:measuredPub` ("PUB" for "Pub") also differ trivially. Round 1's script did not compare meaning strings; I did.
7. **Study citation.** `QRO-0.md:3356` cites `bundle.py:7` for "the commitment binds the QPY file's own digest". At 3a73823 that sentence is at `bundle.py:17`, and P1 cites `:261-268` for the composition (READ).
8. **Runner prose.**
   - `run.sh:29`, the fingerprint comment at 170-174 (which says "never its path" for moth, while the engine's path is recorded), and the `--resume` refusal at 205 do not name the engine.
   - A resume under another engine is refused correctly, but the message lists the other causes.
9. **Timing.** CLAUDE.md's "~125 s" is below every full run this round: 133 s and 141 s by the lead, 159 s mine (loaded), 140 s for the 24-stage stand-in run. The times are noisy (BELIEVED), and the lead's 01:31:41Z entry says they wait on an idle run.
10. **Cosmetics.**
    - A version given as the JSON number `0.1` is refused `context` with "declares 0.1; this reader reads 0.1" (MEASURED). That follows D10, but the detail reads as self-contradictory.
    - `reader.py` line 16 is 186 characters.
11. **Old Python engine.** The fingerprint's `f"{d.metadata["Name"]}"` is Python 3.12 syntax (PEP 701, BELIEVED). An engine older than 3.12 would hash a SyntaxError message. The installed engine is 3.12.9 (MEASURED).
12. **GitHub anchors.** "GitHub lowercases a page's anchors" rests on P4's measurement in the ledger (READ). I fetched nothing.
13. **P0.2's part.** I found no fault. I read its round-3 to round-4 diff, and the full suite passes on top of it.

## What I did not do
- I ran no real P1, P2 or P4 code, only stand-ins, and no SHACL engine beyond naming it.
- I fetched no URL and tested no POSIX host.
- I tested no engine on Python older than 3.12 (none is installed) and no engine whose packages change (installing is not allowed).
- My scratch commits have no privacy-gate run over commit history.
- I did not run the lead's `m_p03.py` against the pre-fix code.
- I touched no key, token or CRN. I did not open `~/.quantum-film` or any `.atlas` directory, did not connect to IBM or Atlas, and submitted nothing. The instruments stage and one citation check read moth-quantum read-only.
- **Rule slips.** My first command wrote `/tmp/p03_files.txt` (OS temp). Two file lists were written one level above `check\` and moved in at once. A later command wrote `/tmp/r.out`. Re-running round 1's `atk_p2.py` made a scratch crate under the OS temp directory. I removed all three and the stray lists; the runner's own pytest temp use is as usual.

My scripts and logs are under `SCRATCH\verifier-P03-r2\check\`: `mut\` for mutants and logs, `fz_*.py` for the fuzzers, `cmp_meanings.py`, `cli_cases*.py`, `sanity_cases.py`, `agent_case.py`, `whole.diff`, and the full-run and stand-in logs.
