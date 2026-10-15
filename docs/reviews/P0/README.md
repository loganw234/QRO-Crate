# P0's verifier reports

Each report as its verifier returned it, collected on the date its row gives (P0's verifier, round 5, R5-4).

**Where each came from:** the verifier's final message, read out by the lead, the whitespace around it stripped, and written ending in one line feed.
- Round 1's two arrived as task notifications, so no wrapper is in them. The transport wrote `<`, `>` and `&` as `&lt;`, `&gt;` and `&amp;`, and they are kept as received.
- Rounds 2 to 6 were read from their verifiers' own transcripts, because the harness refused each verifier's write of its report to a file. They hold their verifiers' own `<` and `>`.

**What was changed after that, and nothing else:**
- **A home path is redacted** as `<scratch>`, `<repos>`, `<home-config>` or `<home>` (rule 3).
- **Every other string the privacy gate reads as a home path** is redacted as `<a home path>`: the reports quote examples of home-path shapes, the verifiers' own constructions among them.

The table counts the lead's redactions. A placeholder a verifier wrote itself, `<a home path>` or `<repos>` in its own report, is its text: kept, and not counted (P0's verifier, round 4).

| file | report | collected | its source's SHA-256 | home paths redacted | other strings redacted as `<a home path>` |
|---|---|---|---|---|---|
| [round1-interim.md](round1-interim.md) | P0's first verifier, its interim report: the one P0-1 to P0-8 were first answered from | 2026-10-14 | `0b8205eb…` | 0 | 4 |
| [round1.md](round1.md) | P0's first verifier, its final report: P0-1 to P0-8 and notes N1 to N8 | 2026-10-14 | `6850d3da…` | 0 | 1 |
| [round2.md](round2.md) | P0's second verifier, a scoped re-check: NOT READY, R2-1 to R2-9 and notes 1 to 13 | 2026-10-14 | `90e225a1…` | 1 | 0 |
| [round3.md](round3.md) | P0's third verifier, a scoped re-check: NOT READY, R3-1 to R3-4 and notes 1 to 15 | 2026-10-14 | `5c361d20…` | 0 | 0 |
| [round4.md](round4.md) | P0's fourth verifier, a scoped re-check: NOT READY, R4-1 to R4-5 and notes 1 to 10 | 2026-10-15 | `80690752…` | 0 | 0 |
| [round5.md](round5.md) | P0's fifth verifier, a scoped re-check: NOT READY, R5-1 to R5-5 and notes 1 to 12 | 2026-10-15 | `2aca381b…` | 0 | 0 |
| [round6.md](round6.md) | P0's sixth and last verifier, to the bar Logan set: READY, with its notes on tests and prose | 2026-10-15 | `130e35fe…` | 0 | 0 |
