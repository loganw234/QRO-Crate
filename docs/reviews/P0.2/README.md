# P0.2's verifier reports

Each report as its verifier returned it, collected on the date its row gives.

**Where each came from:** the verifier's final message, read out by the lead from its own transcript, because the harness refused the verifier's write of its report to a file. The whitespace around it is stripped, and it is written ending in one line feed. It holds its verifier's own `<` and `>`.

**What was changed after that, and nothing else:** a home path is redacted as `<repos>` or `<scratch>`, as P0's and P0.1's reviews are (rule 3).

| file | report | collected | its source's SHA-256 | home paths redacted | other strings redacted as `<a home path>` |
|---|---|---|---|---|---|
| [round1.md](round1.md) | P0.2's first verifier, on the full bar: NOT READY, D1 and D2, and notes A to H | 2026-10-15 | `567a8cb1…` | 2 | 0 |
| [round2.md](round2.md) | P0.2's second verifier, on the full bar: NOT READY, two defects (a sentence, a test that read the user's global git ignore file), and notes | 2026-10-15 | `039f450b…` | 0 | 0 |
| [round3.md](round3.md) | P0.2's third verifier, on the full bar: NOT READY, one defect (a broken branch ref read as no history), and notes; the cap reached | 2026-10-15 | `75342a0d…` | 0 | 0 |
| [round4.md](round4.md) | P0.2's fourth verifier, on the relaxed bar: READY, and notes | 2026-10-15 | `32b360fa…` | 0 | 0 |

round2.md to round4.md came from the lead's own transcript, where the harness delivered each verifier's final message inside a task notification. round2.md holds `&lt;N&gt;` as the notification carried it, for the verifier's `<N>`.
