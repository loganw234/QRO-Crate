# P2.2 round 1: verifier report

## Verdict: NOT READY

There is one defect. It is in prose only: docs/P2.md's timing claim for the budget is false for some gate placements. The code, the controls, the tests and the stages held everywhere else I tried. The budget bounds what it says it bounds, which is amplitude passes. The page's time claim is the thing that is wrong.

The freeze matched: SHA256SUMS begins `bf46c3d97e722929` and every file of `tree\` checked out. I ran the full runner in my copy through `sbx-mid.sh`, with `QRO_MOTH_ROOT` and `QRO_SHACL_PYTHON` set (MEASURED, run `20261108-030420-21953-cbc223c`, tree committed as `cbc223c`):

- **24 stages passed, none failed, none skipped.**
- `p2` took 91 s, `p2-crates` 176 s, `p4` 156 s, `p4-shacl` 170 s. These ran beside my own work.

## Defect

**D1 (prose): the page's time claim for the budget is false.**

docs/P2.md limit 13 says "a pass costs … 180 ns to 210 ns for a dense 4 x 4, on 16 to 20 qubits, on this host quiet (MEASURED …), so 2^28 passes is under a minute here". The "Step 7 / what it costs an honest crate" paragraph says the same. This holds for typical placements and not for adjacent low qubits.

- **Instrument:** I timed `p2_sim.simulate` pass by pass with my own scripts (`ns_per_amp.py`, `worst.py`).
- **Slow placements** (MEASURED, quiet re-run after the runner ended):
  - A two-qubit block on qubits (0,1) of a 20-qubit state costs 1.7 µs per amplitude.
  - At 16 qubits, an unfusable alternation of cz(0,1) and cz(0,2) costs 0.70 µs.
  - Typical placements cost 0.08 to 0.24 µs, so the page's figure is right for those.
- **Cause:** `_quarters` and `_within` build one small slice group per quarter when the high and low axes are adjacent and low.
- **Crate just under the budget, run through the CLI:**
  - I replaced the twin's morning known-answer gate list with a 16-qubit one. Headroom was 250,339 passes.
  - With the worst placement it took **236.5 s** (loaded), with exit 1 and a refusal `(a)`.
  - A random list of the same price (headroom 264,419) took 47.4 s.
  - The page's "under a minute, quiet" is therefore wrong by about 4 to 8 times for the worst placement.
  - At 20 qubits, 256 passes of the (0,1) block come to about 7 minutes quiet.
- **Fix:** restate the time bound as a range that names the placement. The code needs nothing.

## Findings by scope item

**1. The budget (code right).**

- **Count** (MEASURED, `count.py`):
  - On the twin, step 7 counts 7,479,370 and step 6 counts 1,294,892, matching the page.
  - Both are identical in a fresh process, warm, and after `p2_sim.clear()`.
  - Counts are order-independent.
- **Price against work:**
  - My instrument counts the real amplitudes touched in `_apply1` and `_apply2` by `len(psi)`, `State.work`, and the price. All three are equal, with 0 mismatches. The runs were:
    - 1,500 random gate lists;
    - 600 sx, rz and cz mixes built to give exactly-monomial fused blocks;
    - 7 hostile lists;
    - 1,500 random logical circuits, split into core and tail.
  - `simulate` and `cost` both call `enters`.
  - Nothing the simulator does exceeds its price except constant factors. The only large one is D1.
- **Refusal:**
  - A crate over the budget by 263,965 passes gave exit 1 in 1.3 s: `REFUSED compile-uncontrolled at …/bundle/known-answer.gates.json: holding it would bring this crate's exact hold to 268699421 amplitude passes, past the 268435456 that qro-exact-hold/1 allows a crate; nothing past it is simulated`.
  - The spend comes before the hold (the "spend-after-hold" mutant is killed).
- **Pair key `(gates, circuit, role, basis)`:**
  - It is complete: `hold_circuit` reads only those, plus the check's one law.
  - On the twin, a law pair named again as a known-answer or a coherence circuit is refused `(b)` or "cannot be held". A coherence pair named again with a different basis (S4) passes legitimately, because the XX and YY parities are both 0.375.
- **Meanings:**
  - The two strings in qro/vocabulary.py are the lead's words exactly.
  - REFUSALS.md and VOCABULARY.md changed in those two rows alone. CONTROLS.md and profile/ are byte-identical to main.
  - The runner's `vocabulary` and `profile` stages passed.
- **Step 6** is priced from zero, apart from step 7, and spent before `law_circuit_problem`. The "spend after problem" and "spend skipped" mutants are killed.

**2. Controls (MEASURED, `plantdiff.py`).**

- `class-declared` changes `ro-crate-metadata.json` alone. The CLI gives exit 1: `measure-class at #contrast-n-crystal-share-uniform qro:class`.
- `compile-broken` changes the law gate list, the three bundle manifests, the lines and markers, and the metadata (13 files). The CLI gives exit 1: `compile-uncontrolled at …/bundle/law.gates.json`, `(a) … 2.313e-03`. No earlier step refuses it.
- Both come from P1's twin, which is accepted. `controls/registry.py` is unchanged and `plants()` joins both.
- A plant on a crate it was not written for raises `PlantError` before its first write.
- **P4 gate (note, MEASURED once):**
  - No P4 test reads these two refused plants; `accepted_control_problems` walks only `accepted` rows.
  - No must shape fails on either planted crate, checked by `must_failing` over the expansion.
  - No test holds this, so it could change later without any test noticing.

**3 and 4. Twin tests and p2-crates.**

- `p2-crates` passes in the runner.
- I read the interval and control tests. They are tight: the 70 intervals are held to 2^-48 plus slack, and the instrument's printed lines are reproduced word for word.
- **Builder's survivor F1** (the floor's rank one lower) moves the 95th percentile below the fourth printed place. The page's figure comparison cannot see it, and P2.1's rank test holds it. I judge this a note, not a defect.

**5. `tests/p2/data/` removed.**

- All 10 of main's copies equal the twin's files byte for byte (MEASURED, 10 of 10).
- No test or document still reads a removed path. The one mention, in docs/VALIDATION.md, is main's own historical entry.

**6. N1 to N4 and N7.**

- 11 bound mutants (N1 gate cap, N3 zero widths, N2 each index edge, N4 crystals, observable edge, memo 64) are all killed.
- All P2 files are ASCII and LF (MEASURED).

**7. Registration.** `register_p2.py` is unchanged. Only steps 6 and 7 are touched. The `twin` stage passes, and `p1`, `p1-crates`, `controls`, `controls-run` and `privacy` pass.

**8. Hostile input** (MEASURED through the CLI as a process).

- Exit codes were 0 and 1 only.
- The budget refusal is by step name, not a crash.

**9. Stated limits.** Limits 12 and 13 hold in their count claims. Limit 13's time wording is D1. Citations: all 255 test names in docs/P2.md exist and name the right file (`cites.py`). `test_each_built_control_comes_out_as_section_11_says` is in `tests/controls`, as the page says.

**10. Whose files.**

- All 35 paths are P2's own or within the lead's grant.
- `test_p2_steps.py`, `test_p2_register.py` and `test_p2_contract.py` are main's, byte for byte.
- The four changed P2.1 test files differ only by the removed data and N7.

**11. Junctions.** P2's code uses hard links only: no junction, symlink or `mklink`. I made none.

**12. Privacy.** The tree and the builder's `p22` scratch hold no IBM job id and no `records/` name. The `privacy` stage passes.

**13. Mutation.**

Killed, all by P2 tests, by my own selection beyond the builder's 40:

| group | mutants | killed |
|---|---|---|
| pair key short of each part | 6 | 6 |
| manifest cache key | 1 | 1 |
| price and cost divergences | 10 | 10 |
| spend order and budget handling | 7 | 7 |
| non-local carried digests | 1 | 1 |
| memo-dependent spend | 1 | 1 |
| N1 to N4 bounds | 11 | 11 |

Zero survivors. Logs: `mut1.log`, `mut2.log`, `mut3.log`.

## Notes (below the bar)

- **Reading cost** (MEASURED, loaded): a 99,920-cz gate list took 3.7 s to read and fuse, 37 µs a gate. The page says about 22.5 µs a gate and about 2 s a file. The 256 price still covers it, but not twice over for that mix.
- **P4 reach:** no test would notice if a must shape began failing on a refused crate plant.
- **F1** is judged above.
- **Quick budget:** P2's own `p2` stage took 91 s here and is the lead's call at the merge. I did not time the quick budget.

## What I did not do

- I did not run the lead's `84b3054` laying, or an idle full run. My runs were beside my own mutant jobs, so the stage times are loaded.
- I built no crate of 25 to 37 device compiles. The 25 to 37 range is checked by arithmetic and the p2-crates test.
- I ran no step-6 CLI crate just under or over its budget. That path rests on the killed mutants and the P2 tests.
- I made no 20-qubit CLI crate just under the budget. I estimated it by extrapolation.
- I did not try a manifest of millions of entries. The page leaves manifest parsing uncounted.

Notes and scripts are in `<scratch>\verifier-P22-r1\check\notes.md` and `<home>AppData\LocalLow\qro-sbx\p22-r1\scripts\`.
