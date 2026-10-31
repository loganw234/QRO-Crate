# P2.1 verifier, round 2: NOT READY

The code gave no wrong answer on anything I tried. It matches the first verifier's tree byte for byte except for the two removed dead names. Round 1's fixes hold. Two gates still pass faults that `docs/P2.md` says its tests catch (D1, D2), and one stated limit is false (D3). None of the three is about what the code does.

## Freeze and runs
- **Freeze (MEASURED).** `sha256sum -c` over `frozen\tree` is 324 of 324 OK, and SHA256SUMS.txt begins `11c633ae92da97d1`. Every packet file's hash matches the brief, and the worktree's files equal the frozen tree. My working copies still match all 324 after my runs.
- **Against 37640f0 (MEASURED, `git archive` and `diff -rq`).** P2.1 adds `docs/P2.md`, seven `qro/p2_*.py`, `qro/register_p2.py` and 24 files in `tests/p2/`. It changes only `docs/README.md`, by one bullet over two lines. Against the first verifier's tree, only `Law.index` and `_MEASURE` differ, so round 1's evidence about the code carries over.
- **Runner (MEASURED).** I ran `sbx-mid.sh bash verify/run.sh` on a committed copy (856d19b). Run `20261026-120652-35082-856d19b`: 19 passed, 0 failed, 5 skipped by name (p4, p1-crates, p2-crates, profile, p4-shacl), exit 0. The p2 stage passed 492 tests in 46.55 s.
- **Order (MEASURED).** Each test file passes alone (13+19+3+66+6+51+71+24+26+11+105+97 = 492), and the stage passes in reverse file order.

## Defects

**D1 (gate). Step 7's loops are held by no plant beyond the first Compile and the manifest's entries 2 and 3.**
- **Fault (MEASURED, my harness `v\mut\hm2.py`, baseline first).** Four one-line mutants of `qro/p2_steps.py` pass all 492 tests:
  - U1: only the first Compile by id is held (`[:1]` on the Compile loop).
  - U4: the manifest's last entry is not held (`named[:-1]`).
  - S1: its first entry is not held (`named[1:]`).
  - S2: a known-answer gate list is never held.
- **What each lets through (MEASURED, `v\gap_probe.py` on `v\roots\u1,u4,s1,s2`, every digest made to agree).** A broken carried gate list that the shipped code refuses:

| broken carried list | shipped | U1 | U4 | S1 | S2 |
|---|---|---|---|---|---|
| `sheet-01/known-answer.gates.json`, the second Compile's own | refused at that list | accepted | refused | accepted | accepted |
| `bundle/coherence-yy.gates.json`, the manifest's last entry | refused | refused | accepted | refused | refused |
| `bundle/known-answer.gates.json`, its first entry | refused | refused | refused | accepted | accepted |

- **Why the tests miss it (READ).** Every step-7 plant breaks `bundle/law.gates.json` or `bundle/coherence-xx.*` of the small crate (`test_p2_steps.py` lines 371 to 413 and 553). The `sheet` crate appears only in honest tests.
- **Claims it contradicts.** The page says "Then, for each Compile ... every gate list it names that the crate carries is held, whatever any claim says", and "Every claim here is held by a test or says it is not". Round 1's D1 was the sibling of this.
- **Fix.** Three plants, each refused `compile-uncontrolled` at the broken list: the sheet's own known-answer list, `coherence-yy`, and the small crate's known-answer list. `break_list` in `v\gap_probe.py` is a recipe. They kill U1, U4, S1 and S2.

**D2 (gate). Three memo-key components are held by no test.**
- **Fault (MEASURED).** Three mutants of `qro/p2_hold.py` pass all 492 tests:
  - K6: the comparisons' key `(gate digest, n, ops)` without `ops`. S5, with `len(ops)`, also passes.
  - K7: the judgements' key without `named.role`.
  - S4: the same key without `circuit.n`.
  - S3, which drops `n` from the comparisons' key, is equivalent, because the width check comes before the lookup.
- **What each lets through (MEASURED, `v\memo_probe.py` and `v\memo_probe2.py` on `v\roots\k6,k7,s4`).** A crafted crate that the shipped code refuses:
  - K6: one carried gate list named twice, with two logical circuits of one width, the second not its circuit.
  - K7: a law circuit named again as a coherence circuit with the same basis string.
  - S4: the 4-qubit law circuit, then the same operations on 5 qubits as a law circuit.
- **Claim it contradicts.** Limit 12 says the memo is "keyed by the bytes step 7 read itself, so no crate can move another's verdict", and cites `test_the_steps_memos_never_change_a_verdict`. That test runs one honest and one broken crate cold and warm, so it holds only the gate list's digest. `test_two_circuits_of_the_same_operations_are_each_held_at_their_own_width` uses only known-answer circuits, whose verdict is the same at every width.
- **Fix.** Three tests on those three crates.

**D3 (prose, a stated limit). Limit 13's first sentence is false: "Cost grows with the distinct gate lists and with their width".**
- **LRU thrash (MEASURED, `v\thrash.py`).** The memo is an LRU of 64. K Compiles share a manifest that names N distinct gate lists. At N = 64 the simulator runs 64 times for any K. At N = 65 it runs 65 times at K = 1, 195 at K = 3 and 390 at K = 6.
- **Per reference (MEASURED, `v\refcost.py`).** Every manifest entry parses its logical circuit again, memo or not. A 99,990-gate pair costs 0.264 s a reference, of which `read_qasm` is 0.245 s.
- **Files times Compiles (MEASURED, `v\quad.py`).** The set of carried digests is rebuilt over every File for every Compile: 1.8 to 4 microseconds per File per Compile (2,000 Files and 200 Compiles take 0.73 s). Larger sizes are BELIEVED.
- The cost stays bounded, so this needs a restatement, not a hang fix. The budget the lead leaves open for P2.2 should count references, not distinct lists.
- The page's numbers are true within noise (MEASURED, the builder's `cost13.py` on my copy):
  - 70 gates in 10 passes took 0.9 s.
  - 416 gates in 76 passes took 28.9 s (page: 32 s).
  - One 20-qubit pass took 1.0 to 1.35 s (page: 1.3 to 1.7).
  - Memo entries hold 8.5 and 56.5 MiB (page: 57).
  - The 12 to 47 hour figure and the 3.5 GiB are extrapolations (BELIEVED) and were not run.

## Round 1's fixes hold
- **Mutants (MEASURED).** The builder's 27 are each killed by the test they name. The first verifier's nine unrun ones (H65, H66, H68 to H74) are all killed. Its live ones (H6, H8, H20, H33, H41, H60, H62, C1, C2, C2b, C3, C7) are killed by the new tests.
- **Citations (MEASURED, `v\doc_cites.py`).** The page cites 111 test names plus four prefixes such as `test_t2_`. Every name exists in the file the page gives. All 71 quoted plant keys exist, and every plant is cited. D6 is met for citations but not for D1 and D2 above.
- **Limits.** Limit 16 is true as worded (see note 1). Limit 13's numbers are true; its first sentence is D3.

## What I tried and could not break
- **Classes and values (MEASURED).**
  - 1,818 metadata edits of every CHECKED term of the 30 entities that carry P2 terms, on the small crate and on the real crate, through the whole checker with a pass-through generator.
    - Edits were neighbours, alternative spellings, type confusions and deletions.
    - Refusals were `measure-class` 471 and 477, `spelling` 1,319 and 1,313, `graph-form` 10, `compile-uncontrolled` 7 and `step-unbuilt` 10.
    - The one "accepted" was my writer re-sorting the twins list. The raw bytes with the twins reversed are refused `spelling` (`v\twins_probe.py`).
  - 214 edits of the raw results (a shot moved, added or dropped) with digest, size and `qro:shots` made to agree. 169 were refused `measure-class`. The 45 accepted change nothing P2 measures, by my recomputation.
  - My own kernel and exact determinants give P2's law table in all 4,368 layouts. The raw bytes of kingston, marrakesh and fez, decoded by me, equal the records' counts. 21 real and 2,800 random measures equal my formulas exactly.
  - The page's table of v0's classes and values is true. The law file is 78,482 bytes with the stated digest.
- **Intervals (MEASURED, `v\iv_ref.py`, decimal at 110 digits).**
  - 1,900 cases covered p = 0, p = 1, n = 1, n up to 1e20, six families, five alphas and fractional totals. Every end is on the 2^-48 grid, contains the KL set and equals the ideal grid end.
  - Kingston less fez at family 70 is the pinned `[12330612205551/2^48, 16819644152847/2^48]`.
  - 506 intervals hash identically under Python 3.12.15 and 3.13.5.
- **Simulator and hold (MEASURED, my numpy simulator).**
  - 300 random gate lists agree within 1.4e-15, 300 random circuits within 5.6e-16, pair expectations within 2.1e-14, and the 16 distinct real files within 1.0e-17.
  - All 124 real manifest entries (12 distinct) hold, worst difference 5.4e-17.
  - Cold and warm memos give the same bytes (900 of 900).
- **Hostile files as processes (MEASURED).** 18 cases (law, manifest, gate list, circuit) all exit 1 with one REFUSED line by the step's name.
- **Data and files (MEASURED).**
  - The ten copies equal `git show 3a73823:&lt;path&gt;`.
  - They hold no job id, key shape, home path, CR or BOM.
  - The runner's privacy stage read 324 files and 1 commit message.
- **Mutation (MEASURED).** 664 mutants in all.
  - Every site of `p2_steps` (219) gave 215 killed and 4 live, all equivalent or message-only.
  - Every site of `p2_interval` (188) gave 179 killed and 9 live, all equivalent or exact ties.
  - Samples were `p2_law` 46, `p2_sim` 64 and `p2_report` 18.
  - Ten `//` to `/` mutants of `p2_interval` were all killed by the numeric tests.

## Notes (below the bar)
1. **Limit 16's definition of an orphan leaves out a gate list listed in a Compile's `object`.** A broken one there, unnamed by the manifest, is accepted. In `result` it is refused (MEASURED, `v\orphan_probe.py`).
2. **No step-level plant edits any term of the `y0y1`, `n-crystal-share` or `nn-pair-correlation` Measurements.** Mutants that skip their comparison are live. The code takes one generic path for all measures (READ).
3. **Two performance mechanisms are held by no test.** The LOGICAL and CORES memos switched off (`p2_sim.py` lines 507 and 510) and `fuse` closing unrelated pending blocks (`q not in p`) both pass. Results are the same, but the page says coherence circuits "resume from the law circuit's memoised core".
4. **A `coherence` Pub on an Atlas raw result is measured as x0x1 from the all-Z layouts (READ).** `pub_counts` ignores the Pub for Atlas, and P1's `account` checks only the law role. No v0 crate has one.
5. **QASM cap (MEASURED).** Exactly 100,000 operations followed by a barrier line is refused "more than 100000 gates". Barrier lines are uncapped; 300,000 were read.
6. **The independence test would miss an integer `/`** (round 1's note). The numeric tests catch it.
7. **Equivalent or unreachable live mutants.** These are a `&gt;` to `&gt;=` tie in `outside()`, `e &gt;= 0` at e = 0, forced-True memo guards, and the reader's one-qubit boundary.

## What I did not do
- I ran no P1.2 generator, twin, control or `p2-crates` stage (not in the packet), and I did not run the quick budget separately.
- I tried only a second interpreter on this host (3.13.5, same libm), not a second host.
- I did not run the 12 to 47 hour gate list or 64 large memo entries.
- I did not repeat the first verifier's every-site run of `p2_hold`, `p2_measures` and `register_p2`.
- **Slips.** Early on I wrote two path listings to Git Bash's `/tmp`, outside the sandbox: `/tmp/wt_files.txt` and `/tmp/frozen_files.txt`. They hold paths only, and I left them in place. My first pytest and runner runs used the shared sandbox temp. I stopped several of my own hung mutant test processes, two by hand and the rest by a watchdog, by their workspace path, and counted them detected.
- **Report file.** The harness refused my Write of `report.md` ("subagents return findings as text"), so this message is the report.
- I printed no IBM job id. I opened nothing under `~/.quantum-film`, used no key or network, and edited nothing outside my sandbox and check directory.

## Where things are
- **Check directory:** `<scratch>\verifier-P21-r2\check\`, with `notes.md` and `fix-recipes.md`.
- **Fix recipes:** `fix-recipes.md` holds the exact mutant snippets and the crate recipes for D1 to D3.
- **Scripts, mutant lists and logs:** `<home>AppData\LocalLow\qro-sbx\p21-r2\v\`, `...\v\mut\` and `...\logs\`.
