# P2.1 verifier, round 3: READY

**Verdict: READY.** I found no defect in what the code does, in a gate, or in prose, at the full bar.

- Every round-2 fix holds, and the second verifier's live mutants are all killed by the new tests.
- None of the three new refusals refuses what an honest crate holds.
- Everything I found is below the bar. It is boundary reach of the readers (the code is right at each boundary) and two small API and prose items, all under Notes.

## Freeze and runs

- **Freeze (MEASURED).**
  - Every packet hash matches the brief. SHA256SUMS begins `d0bdfcef735f860a`.
  - `sha256sum -c` over `frozen\tree` is 324 of 324 OK, and the tree holds exactly those files.
  - The worktree equals it. `diff -rq` shows only `.gate-state`, which git ignores. HEAD is 37640f0.
  - My working copy was still 324 of 324 at the end.
- **Against 37640f0 (MEASURED, `git archive` and `diff -rq`).**
  - P2.1 adds `docs/P2.md`, the seven `qro/p2_*.py`, `qro/register_p2.py` and 24 files in `tests/p2/`.
  - It changes only `docs/README.md`, by one bullet.
  - The 23 Python, test and doc files it adds or changes have no CR and end in LF. The ten data files have no CR, no non-ASCII byte and no BOM.
- **Runner (MEASURED, `sbx-mid.sh`, copy committed as 8d690de).**
  - Full run `20261026-143800-42814-8d690de`: 19 passed, 0 failed, 5 skipped by name (p4, p1-crates, p2-crates, profile, p4-shacl), exit 0. The p2 stage took 37 s.
  - Quick budget `20261026-155434-13350-8d690de`: 16 passed, 0 failed, 2 skipped by name (p4, profile), exit 0.
  - tests/p2 holds 509 tests. Each file passes alone, and the stage passes in reverse file order.

## Scope 1: round 2's fixes and the three changes

- **Mutants (MEASURED, the second verifier's definitions, my harness).**
  - I ran 27: U1 to U4, S1, S2, S2b, S2c, S4 to S8, K6 to K8, GL1, LC1, LC2 and the seven Measurement mutants.
  - 26 are killed by the stage, each by the round-2 test the brief names where it names one. Examples: the sheet's own known-answer plant kills U1; "the manifest's last gate list broken" kills U4; "the manifest's first gate list broken" kills S1 and S2.
  - The one live mutant is S3, the comparison memo's width. It is equivalent, because the width check precedes the lookup.
- **The three behaviour changes refuse nothing an honest crate holds.**
  - *Atlas coherence Pub.*
    - P1 gives the Atlas crate six law Pubs and one known-answer Pub, and no coherence Pub (READ, ledger-P1 §1.3).
    - I ran the six real Atlas law results through the builder's Atlas-shaped crate (MEASURED, `atlas_real.py`). Steps 6 and 7 accept all six. The values are sensible: forbidden-share 0, XEB 0.98 to 1.05, nearest-neighbour correlation 0.629 to 0.641 against the law's 0.64.
  - *Gate list in a Compile's `object`.* P1's Compiles list the manifest and logical circuits there and the gate lists in `result` (READ, ledger-P1 lines 438 and 1489). The real, sheet and small crates pass.
  - *QASM cap.* v0's circuits are at most 311 lines. I probed the shipped reader at the boundaries (MEASURED). It reads exactly 100,000 gates and a trailing barrier, and refuses the 100,001st gate and the 100,001st barrier line.
- **docs/P2.md.**
  - It cites 124 names; all exist. The one that is not a function is a file name.
  - I read each cited test's opening against the claim it backs. Each memo key part has a killed mutant behind it (S4 to S8, K6 to K8, GL1, LC1, LC2).
- **Limits 10, 12, 13 and 16 are true.** Details are under Scope 5.

## Scope 2: classes and values

- **Edit matrices (MEASURED, `edit_matrix.py`).**
  - I made 6,866 in-memory edits of every P2-owned term, keeping only values the reader's spelling rules accept (small 1,817, Atlas 1,291, sheet 1,946, real 1,812). There were no crashes.
  - Both steps accepted exactly one edit per crate (not Atlas): `qro:lawCircuit` re-pointed to `bundle/law.qasm`, an equivalent circuit in the question's object. That is the first verifier's note.
- **Raw edits with digests resealed (MEASURED, `raw_matrix3.py`).** 229 edits: 189 refused, all `measure-class`; 40 accepted. Step 6 refused exactly when a measure's value or in-scope count changed.
- **Metadata read.** Step 6 reads only `qro:role`, `qro:basis` and the graph relations from the metadata (READ). Step 5 holds the bit order, and step 9 covers the READ terms.
- **Independent values (MEASURED).**
  - `values_ref3.py`: 6,300 values on random counts against my exact formulas, 0 differ.
  - `law_ref.py`: my kernel and determinants give the law file's 78,482 bytes and digest `a242c4de…`, all 4,368 layouts, 1,360 forbidden, and all 20 Contrasts.
  - `law_circuit_check.py`: my numpy simulation of the source circuit lays the kernel law to 3.6e-17, with X0X1 = Y0Y1 = +0.375.
  - `law_ref_small.py`: the Contrasts agree on the test suite's small law, a one-crystal law and a 3x3 law.

## Scope 3: certified intervals

- **Containment and tightness (MEASURED).**
  - `iv_check.py` uses my own mpmath bisection at 90 digits on 2,644 cases: p = 0, p = 1, n = 1, n up to 2^63−1, families 1 to 10^6, seven alphas, and fractional totals.
  - Every interval contains the KL set, every end is on the 2^-48 grid, and every end is the ideal grid end.
  - `pipe_check.py` covers 400 random trials of counts through value, family and certified interval, mapped to units: 0 problems.
- **Host independence.** Python 3.13.5 recomputes all 2,644 intervals with 0 differences from 3.12.15. The metadata P2 writes is the same bytes under `PYTHONHASHSEED` 0, 1 and 4242. `p2_interval.py` imports only `dataclasses` and `fractions` and has no float, no libm and no true division on integers (READ).

## Scope 4: simulator, hold, memo

- **Simulator (MEASURED).**
  - Against my own numpy reader and simulator, worst differences are 1.6e-15 on 120 random gate lists and 4.4e-16 on 120 random circuits. The gate lists use permuted clbits, early measures and tiny angles. 440 pair expectations differ by at most 8.9e-16.
  - On v0's real files read in place (12 gate lists of the three devices and 4 circuits), the worst difference is 9.5e-18.
  - Cold and warm memo bytes are identical.
  - All 31 real manifests (124 entries) read, and every digest they name is a blob of the tree.
- **Memo across crates (MEASURED, `memo_xcrate.py`).** I built 21 honest and faulty crates, took their verdicts cold, then replayed them warm in 6 random orders (126 replays). 0 verdicts differ.
- **Unusual honest crates (MEASURED, `edge_honest.py`).** I built six: no N-crystal shot, all forbidden, a single outcome, one shot, parities of ±1, and 170,000 shots. Steps 6 and 7 accept all six.

## Scope 5: the rest

- **Entry rule (MEASURED, `poison_probe.py`).** P0's fixture is accepted (exit 0, digest `21fafec5…`) with every `qro.p2_*` import blocked. A crate carrying P2's entities under the same block exits 3, "the checker itself failed".
- **Hostile inputs as processes (MEASURED, `hostile_proc.py`).** 43 hostile files (law, law circuit, logical circuits, manifest, gate lists) all exit 1 with one REFUSED line by the step's name, or are honestly accepted. There was no exit 3, no exit 120 and no hang.
- **Exit codes.** The command line escapes everything outside printable ASCII (READ). Each honest crate shape (small, sheet, Atlas, real) passes steps 1 to 8 as a process and stops only at the unregistered test generator.
- **One spelling per value (MEASURED, `spelling_probe.py`).** 33 alternative spellings of P2's terms are refused at step 1. The exception is a `holdRule` in another case, which the reader reads as plain text and step 7 refuses as `step-unbuilt`. The twins list in reverse order is refused when written into the raw bytes.
- **Contract with P1's generator.** T1 to T4 and the two-argument `contribute` call are held by tests I read (READ).
- **Data (MEASURED).** All ten copies equal the README's size and SHA-256 and equal `git show 3a73823:path` in moth-quantum. The README's commit and MIT text equal moth-quantum's. No Moth or Atlas string, and no 18 to 22-character token, appears in them.
- **Limit 13 (MEASURED).**
  - The thrash counts are exactly the page's: 64, 64, 65, 195 and 390 simulations, and 64, 192, 65, 195 and 390 parses.
  - Memory entries are 8.5 and 56.5 MiB, exactly the page's.
  - Timings were taken on a loaded machine and are within noise: a reference to a 99,990-gate pair 0.26 s (page 0.19 to 0.20 s); files times Compiles 2.05 to 3.54 µs (page 1.7 to 3.3); one 20-qubit pass 0.4 to 1.1 s (page 1.3 to 1.7 s).
  - The 12 to 47 hours stays BELIEVED (extrapolated, never run), as the page says.
- **Report functions (MEASURED).** `floor(14979)` gives 0.1726 / 0.1764 and `floor(24576)` gives 0.1319 / 0.1350, matching the design's printed pairs.

## Scopes 6 to 9: other files, unintended changes, mutation, prose

- **Other files.** No file of another parcel changed (CLAUDE.md item 7).
- **Dead code.** `Law.index` and `_MEASURE` have no remaining reference. No unreferenced top-level definition, no suppression, no TODO, no debug leftover, and no `assert` in production code.
- **Mutation (MEASURED, `hm3.py` harness).**
  - I ran 777 mutants: 27 named, 519 at every site of the operator set in `p2_sim`, and 231 in `p2_law`.
  - 718 are killed and 59 are live.
  - 44 of the live ones are equivalent, unreachable, dead or message-only. 15 are bounds that no test pins, listed in N1 to N3 and N5.
- **Prose.** Spot-read module docstrings and test names against the code. I found no false claim.

## Defects

None.

## Notes (all below the bar)

- **N1 to N3: gate reach, code right (MEASURED probes of the shipped code at each point).**
  - N1: `p2_sim.py:142`. A gate list of exactly 100,000 gates is read by no test. `test_the_gate_lists_caps` sets the cap to 5 and reads a 6-gate list, and the `&gt;` to `&gt;=` mutant survives. The shipped code reads 100,000 and refuses 100,001.
  - N2: `p2_sim.py:233` (cx control and target), `238` (ry) and `243` (barrier). The hostile matrix tests `cx q[5]`, `ry … q[3]` and `barrier … q[4]` against n = 2, and only `x q[2]` at the boundary. The shipped code refuses index == n for all four.
  - N3: `p2_sim.py:128`. The one-qubit and one-clbit boundary is unpinned. This is the second verifier's note 7.
- **N4: gate reach in `p2_law.py`, code right.**
  - Unpinned: crystals = 1 (line 224), denominator = 1 (227, same verdict either way), the observable range edge (256, same verdict), and the 64-entry bound of `_CLASSES` (366, three mutants).
  - `pair.get(p, 0)` (325) is the default for a neighbour pair never co-occupied. No test fixes its value on a non-v0 law. I recomputed it on the test suite's small law (NN value 1/2) and it is right.
  - `_det`'s pivot swap and `law_parts`' self-check are reached by no minor of v0's kernel. I checked `_det` on 4,000 random sparse integer matrices (1,003 with a zero leading pivot) against an exact determinant: 0 differ.
- **N5: code, API leniency.** `p2_interval.pooled` accepts a float or bool total through `Fraction(t)`, where `interval()` raises "never a float". Nothing in the tree claims otherwise, and the result is deterministic. P3 should know.
- **N6: unchanged and by design.** `qro:lawCircuit` can be re-pointed to another circuit that lays the law. A law-role manifest entry's basis is never judged, so a 1M-letter basis and a 1 MB circuit name are read.
- **N7: trivial.** `test_p2_law.py`, `test_p2_report.py` and `test_p2_sim.py` each hold one non-ASCII character (2 bytes).

If the lead wants N1 to N4 closed before the merge, each is one test case. None changes a verdict.

## What I did not do

- I ran no P1.2 generator, no twin, no controls and no `p2-crates` stage; they are not in the packet. What P2.1 meets of P1.2 is BELIEVED from ledger-P1's seam.
- I used no second host, only Python 3.12.15 and 3.13.5 on this one.
- I did not run the 12 to 47 hour gate list or 64 large memo entries.
- I repeated none of the earlier every-site runs of `p2_hold`, `p2_measures`, `register_p2`, `p2_steps` or `p2_interval`. The code is byte-identical to what they ran, and I ran the second verifier's 27 mutants against the new tests.
- I did not mutate `p2_report`.
- My edit matrices edit the parsed metadata after the reader's spelling rules; I did not push each one through the reader. The 33 spelling probes went through the reader.

## Slips

- One redirect in my own shell to `/tmp_none` was refused for permissions and wrote nothing.
- I ran `git status` and `git log` inside the P2.1 worktree early on. A later `diff -rq` shows it still equals the freeze.
- I printed once the 8-hex prefixes of six Atlas result file names. They are Atlas job ids; I printed no IBM job id.
- The harness refused a `report.md`, so this message is the report.
- I started no subagent, opened nothing under `~/.quantum-film`, used no key or network, and edited nothing outside my sandbox and check directory.

## Where things are

- **Sandbox:** `<home>AppData\LocalLow\qro-sbx\p21-r3\`.
  - Scripts are in `v\` and `v\b\`, mutation in `mut\` and `mutws\`, and logs in `logs\`.
  - The runner logs are `logs\run-baseline.log` and `logs\run-quick.log`.
- **Notes:** `<scratch>\verifier-P21-r3\check\notes.md`
