# P0.4's verifier reports

Each report as its verifier returned it, collected on the date its row gives.

**Where each came from:** the verifier's final message, which the harness delivered to the lead inside a task notification; the lead read it out of its own transcript. The whitespace around it is stripped, and it is written ending in one line feed. The notification carried a verifier's `<`, `>` and `&` escaped, and each report holds them as it carried them: round1.md holds `&lt;CHECK&gt;` for its verifier's `<CHECK>`, round2.md holds `&amp;&amp;` for `&&` and `&amp;lt;CHECK&amp;gt;` where it quotes round1.md (P0.4's verifier, round 2, N9), round3.md holds `&amp;`, `&lt;` and `&gt;` for `&`, `<` and `>`, and round4.md holds `&gt;&amp;` for `>&`.

**What was changed after that, and nothing else:** a home path is redacted as `<repos>` or `<scratch>`, as P0's and P0.1's reviews are (rule 3). And two strings of round4.md, redacted by P0.6 as `<a home path>`, as P0's reviews redact the shapes they quote: its verifier's examples of two spellings of a home path the privacy gate then missed, a UNC path to WSL with forward slashes and a percent-encoded drive path, each with the placeholder name `name`. P0.6 taught the gate both spellings. The copy pushed in 20d40e6 holds them still, and the gate's `KNOWN` table names that copy, so its scan of the history passes over them by name.

| file | report | collected | its source's SHA-256 | home paths redacted | other strings redacted as `<a home path>` |
|---|---|---|---|---|---|
| [round1.md](round1.md) | P0.4's first verifier, on the full bar: NOT READY, D1 and D2, and notes | 2026-10-16 | `5774f9ff…` | 0 | 0 |
| [round2.md](round2.md) | P0.4's second verifier, on the full bar: NOT READY, one defect (a file or a link at a gitlink's path not read), and notes | 2026-10-16 | `c4bb4f1b…` | 1 | 0 |
| [round3.md](round3.md) | P0.4's third verifier, on the full bar: NOT READY, two defects (a guard call hidden after a quoted `#`; a test that fails on POSIX), and notes; the cap reached | 2026-10-16 | `ed80184d…` | 0 | 0 |
| [round4.md](round4.md) | P0.4's fourth verifier, on the relaxed bar: READY, and notes | 2026-10-16 | `d014f919…` | 0 | 2 |
