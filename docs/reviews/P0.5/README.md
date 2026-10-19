# P0.5's verifier reports

Each report as its verifier returned it, collected on the date its row gives.

**Where each came from:** the verifier's final message, which the harness delivered to the lead inside a task notification; the lead read it out of its own transcript. The whitespace around it is stripped, and it is written ending in one line feed. The notification carried a verifier's `<` and `>` escaped, and each report holds them as it carried them: round1.md holds `&lt;tree&gt;` for its verifier's `<tree>`, and `&lt;a&gt;` for `<a>`; round2.md holds `&lt;script&gt;` for `<script>`; and round3.md holds `&amp;` for `&`. round4.md holds none.

**What was changed after that, and nothing else:** a home path is redacted as `<repos>` or `<scratch>`, as P0's and P0.1's reviews are (rule 3).

| file | report | collected | its source's SHA-256 | home paths redacted | other strings redacted as `<a home path>` |
|---|---|---|---|---|---|
| [round1.md](round1.md) | P0.5's first verifier, on the full bar: NOT READY, two defects (a fragment holding `://`, and a last segment ending in `;`, each read otherwise by rdflib), a gate that could not see them, and prose; and notes | 2026-10-16 | `83500274…` | 2 | 0 |
| [round2.md](round2.md) | P0.5's second verifier, on the full bar: NOT READY on prose only, three false sentences (what rdflib reads as written; the first stated limit narrower than its fault; a test comment), and notes | 2026-10-19 | `89349f29…` | 1 | 0 |
| [round3.md](round3.md) | P0.5's third verifier, on the full bar: NOT READY on prose only, two false sentences (item 22's measured claim named RFC 3986 where JSON-LD 1.1 was measured; two test comments), and notes; the cap reached | 2026-10-19 | `5c6e3369…` | 1 | 0 |
| [round4.md](round4.md) | P0.5's fourth verifier, on the relaxed bar: READY, no defect in what the code does; notes (an older hang on a File id of many segments, JSON-LD 1.0's prefixes, two sentences of item 22, test reach) | 2026-10-19 | `77dc76e5…` | 2 | 0 |
