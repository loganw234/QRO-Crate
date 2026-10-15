# P0.1's verifier reports

Each report as its verifier returned it, collected on the date its row gives.

**Where each came from:** the verifier's final message, read out by the lead from its own transcript, because the harness refused each verifier's write of its report to a file. The whitespace around it is stripped, and it is written ending in one line feed. Each holds its verifier's own `<` and `>`.

**What was changed after that, and nothing else:** a home path is redacted as `<repos>` or `<scratch>`, as P0's reviews are (rule 3). Rounds 1 and 2 held none; round 3 held one, the moth-quantum checkout's path in a runner command; round 4 held that one and the scratch directory's.

| file | report | collected | its source's SHA-256 | home paths redacted | other strings redacted as `<a home path>` |
|---|---|---|---|---|---|
| [round1.md](round1.md) | P0.1's first verifier, on the full bar: NOT READY, D1 to D3 and notes 4.1 to 4.3 | 2026-10-15 | `1820c1a9…` | 0 | 0 |
| [round2.md](round2.md) | P0.1's second verifier, on the full bar: NOT READY, R2-1 to R2-3 and notes 4.1 to 4.3 | 2026-10-15 | `dbe9d5ee…` | 0 | 0 |
| [round3.md](round3.md) | P0.1's third verifier, on the full bar: NOT READY, G1 to G3, C1 and P1, and notes 1 to 14 | 2026-10-15 | `0c660c00…` | 1 | 0 |
| [round4.md](round4.md) | P0.1's fourth verifier, on the relaxed bar the cap set: READY, with notes N1 to N8 | 2026-10-15 | `3605736b…` | 2 | 0 |
