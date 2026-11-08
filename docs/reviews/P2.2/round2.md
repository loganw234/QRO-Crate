# P2.2 round 2: READY

I found no defect in what the code does, in a gate, or in prose. All three time passages are true, and the budget bounds what it says it bounds. The notes below are for the lead to take afterwards.

## The freeze and the runner

- **Freeze.** SHA256SUMS begins `e4c1a5df7d4c9e88`, and every file of `tree\` matches it (MEASURED, `sha256sum -c`). Against round 1's packet only `docs/P2.md` and `tests/p2/test_p2_budget.py` differ. In the test file the change is two docstrings, with no code.
- **Files outside P2's.** Against main at 35be18e, P2.2 changes only P2's files, `docs/REFUSALS.md` and `docs/VOCABULARY.md`, and `qro/vocabulary.py`. In `qro/vocabulary.py` only the two granted meanings differ (MEASURED, blob hashes and `diff`).
- **Worktree.** The 12 mismatches against QRO-Crate-P2.2 are P4.3's files, which sit on main after eff2469. Every P2 file matches.
- **Runner.** I committed my copy as `0f2f2ae` and ran `verify/run.sh` through sbx-mid with `QRO_MOTH_ROOT` and `QRO_SHACL_PYTHON` set. Result: 24 passed, 0 failed, 0 skipped, run `20261108-042912-27554-0f2f2ae` (MEASURED).
- **Test citations.** A script I copied from round 1 (`cites.py`) finds every test the page cites in the file it names. The four unresolved names are three prefix stems (`test_p2_`, `test_t2_`, `test_b_`) and a control-registry test that lives in `tests/controls/`.

## The restated time claims

I measured the slow and typical placements with `rates.py`, best of 3, after my runner ended. Other sessions were still on the host, so none of this is truly quiet (MEASURED).

| Placement | 20 qubits | 16 qubits | The page |
|---|---|---|---|
| Dense 4x4 on axes (0,1) | 1.62 to 1.69 µs an amplitude | 1.25 to 1.37 µs | 1.6 to 1.7 on 20, 1.3 on 16 |
| Dense on (0,2) or (1,2) | 0.93 to 0.96 | 0.73 to 0.74 | 0.45 to 0.95 with the higher axis at 2 or 3 |
| Dense on (2,3) | 0.54 | 0.50 | same range |
| Dense at the top, or on axes 8 and up | 0.19 to 0.22 | 0.18 to 0.20 | typical by axis 8 |
| cz on (0,1) | 1.19 | 0.82 | 1.17 and 0.84 |
| cz on the top pair | 0.066 | 0.047 | 0.04 to 0.24 overall |
| One-qubit block | 0.10 to 0.13 | 0.09 to 0.11 | inside the range |

- Nothing I tried at 20 qubits was slower than 1.7 µs, and small dense states are no worse per priced unit. The cost per amplitude at (0,1) is 1.2 to 2.3 µs at 3 to 14 qubits, but the price adds 256 per gate for reading, which dilutes it.
- **Worst cases.** The page's arithmetic is right: 2^28 × 1.7 µs is 7.6 minutes, ×2.1 is 9.4, and the two steps come to about 15 and 19. A law circuit has at most 16 qubits: the tile is L×L with L×L at most 20, and a circuit of any other width is priced at its reading alone. That gives step 6 about 5.8 minutes.
- **Hostile docstrings.** `hostile_list` simulated in 115.7 s and `hostile_law_circuit` in 119.6 s, run two at once. "About 1.5 to 2 minutes" holds, at the upper edge for the law circuit (MEASURED).
- **Reading bullet.** A list of 99,903 cz gates took 3.0 s in the cost walk, which is 30 µs a gate against the page's 37. A list of sx and rz took 2.3 s. A cold hold took 4.3 s on 3 qubits. So "2 to 4 s a file" holds. A 99,990-line logical circuit costs 18 µs a line, well inside the 256 price (MEASURED, `tiny.py` and `qasmread.py`).

## Where round 1 did not reach

- **Step 6 just under and just over, through the command line.** I replaced the twin's law circuit with a 16-qubit one and resealed the digest.
  - Over, in both variants: exit 1 in 1.1 to 1.2 s, `REFUSED measure-class at #question qro:lawCircuit`, "…past the 268435456 that qro-measures/1 allows a crate; nothing past it is simulated".
  - Under, random placement (price 268,381,708): simulated for 108.4 s, then refused at the same place, because the law is not the question's circuit's. That is a different detail, as it should be.
  - Under, slow placement (price 268,409,100): 286.4 s beside two other heavy processes, refused the same way. That fits inside the page's 6 minutes quiet.
- **A step-7 crate at 20 active qubits, just under.** It had 250 reps of cz (0,1) and cz (0,2) alternating, price 267,734,269. It took 265.2 s beside one or two other heavy processes, then was refused (a) after the full simulation. The page's 7.5 minutes is an upper bound over this.
- **Many device compiles.** I built these from the twin by adding compiles whose gate lists differ only in `global_phase`, with manifest digests resealed. This tests step 7 only: the full checker refuses my synthetic crates at step 9 (`metadata-generated`), so I ran step 7 in-process and the command line past step 8.
  - 34 extra compiles (35 distinct bundles in all) count 261,772,510 and are accepted.
  - 35 extra compiles are refused at `xbundle34/coherence-yy.gates.json`, at 269,251,720.
  - This agrees with the page's "25 to 37 of v0's device compiles" and its arithmetic.
- **A very large manifest.** A manifest with 100,004 entries (111 MB) parses in 2.57 s, and step 7 takes 3.77 s in all. The count is the base plus 16 per entry (9,079,370). Time is linear in bytes, so the page's statement that parsing is uncounted and linear is true. Peak Python heap during the parse was about 2.7 times the file (MEASURED).

## Defects

None, in code, gate or prose.

## Notes

All are prose or reach. The code is right in each.

1. **The "about a minute" covers passes, not the counted reading.** A priced unit is not always a pass. A crate of 100,000-gate cz lists on 3 to 8 qubits costs about 436 to 470 ns per priced unit end to end (the cost walk, a cold hold re-reading the file, and its tiny-block simulation). At the budget that is about 2 minutes, measured beside other work. That is still far under the page's stated ceilings. The reading bullet says two readings "may pass" the 256, which is right but incomplete. One clause on the cold hold's own simulation of many tiny blocks would close it. This is prose.
2. **The 7.5 and 9.4 minutes cannot be reached exactly.** Two consecutive blocks on one pair fuse, so an adversary must alternate pairs. The best alternation (0,1) with (0,2) averages about 1.3 µs, so a step tops out near 6 minutes rather than 7.5. The page states them as "whose every pass sat there", an upper bound, so it is not false. The same goes for the 50 to 61 hours.
3. **Memory is only described for the memo.** The memory bullet covers the memo. A manifest or metadata file parses at roughly 3 times its bytes, which is linear in bytes and the host's, like the other reads.
4. Synthetic extra compiles cannot be accepted by the full checker, because step 9 regenerates the metadata from the records. P2's budget at the command line is therefore tested on the twin's own files, or in-process.

## What I did not do

- I made no mutants. This round's change is prose and docstrings only, and round 1 killed 37 mutants over unchanged code.
- I did not run a full-speed quiet machine. Other sessions were on the host throughout.
- I did not simulate a hostile list or law circuit at the full 2^28.
- I did not re-run the plants, the pair-key parts or the price-versus-work comparison on thousands of lists. The code has not changed since round 1.

Notes are in `…\scratchpad\verifier-P22-r2\check\notes.md`, and my scripts are in `<home>AppData\LocalLow\qro-sbx\p22-r2\scripts\`. I deleted the large generated crates from my sandbox directory and left no junctions.
