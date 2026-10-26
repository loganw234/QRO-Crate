# P0.6's verifier reports

Each report as its verifier returned it, collected on the date its row gives.

**Where each came from:** the verifier's final message, which the harness delivered to the lead inside a task notification; the lead read it out of its own transcript. The whitespace around it is stripped, and it is written ending in one line feed. round1.md holds no escape. The notification carried a verifier's `<` and `>` escaped, and round2.md holds them as it carried them: `&gt;` twice and `&lt;` once, for its verifier's `>` and `<`. round3.md holds `&lt;` three times, `&gt;` four times and `&amp;` three times, for its verifier's `<`, `>` and `&`; where it quotes round2.md's escapes, the `&` of each is escaped again, `&amp;gt;` and `&amp;lt;`. round4.md holds `&lt;` three times, `&gt;` six times and `&amp;` seven times, for its verifier's `<`, `>` and `&`: Git Bash's `<&-` and `>&-`, and `<oid>`.

**What was changed after that, and nothing else:** a home path would be redacted as `<repos>` or `<scratch>`, as P0's and P0.1's reviews are (rule 3); round1.md held none, and round2.md one, as `<scratch>`. Every other string the privacy gate reads as a home path is redacted as `<a home path>`, as P0's reviews are: round2.md's two, where it quotes the two known findings of P0.4's round4.md, each a placeholder path. round3.md and round4.md held none of either, and each is as its verifier returned it.

| file | report | collected | its source's SHA-256 | home paths redacted | other strings redacted as `<a home path>` |
|---|---|---|---|---|---|
| [round1.md](round1.md) | P0.6's first verifier, on the full bar: NOT READY, two defects in the history reader (a name beginning with a line feed passed; a file named HEAD at the root failed a clean tree), two false sentences, and notes | 2026-10-19 | `fcff311e…` | 0 | 0 |
| [round2.md](round2.md) | P0.6's second verifier, on the full bar: NOT READY, a file name the output's code page cannot write crashing the gate's last print where only an earlier commit holds the name, a false sentence, and notes | 2026-10-25 | `ecbe14f2…` | 1 | 2 |
| [round3.md](round3.md) | P0.6's third verifier, on the full bar: NOT READY, round 2's fix crashing the gate where there is no stdout to reconfigure, a false sentence on the `need_env` residual, and notes | 2026-10-26 | `730c1f2a…` | 0 | 0 |
| [round4.md](round4.md) | P0.6's fourth verifier, on the relaxed bar: READY, with three defects of the gate older than P0.6, one contrived crash, and notes | 2026-10-26 | `b87dc345…` | 0 | 0 |
