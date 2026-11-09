# P5.1's verifier reports

Each report as its verifier returned it, collected on the date its row gives. P5.1 is P5's first build, the contributor kit's local route and its crate:
- the unit's recipe;
- the kit, with Quantum-Film's runner vendored byte for byte;
- the unit generator and its guards;
- `kit-dirty`;
- the spend rules, and the real route present and refusing;
- intake.

docs/VALIDATION.md's entry "P3.1 committed; P5.1 merged: the contributor kit's first build" says what it is and what each round found.

**Where each came from:** the verifier's final message, which the harness delivered to the lead inside a task notification; the lead read it out of its own transcript. The whitespace around it is stripped, and it is written ending in one line feed.
- **round1.md is the first verifier's report,** its first message. Its second repeated the verdict while its runner was still going, and is not kept.
- **round2.md is the second verifier's report,** its one message.
- **round3.md is the third verifier's report,** its one message.

**The escapes.** The notification carried a verifier's `<` and `>` escaped, and each report holds them as it carried them:
- round1.md holds `&lt;` and `&gt;` twice each, in its verifier's `at &gt;= 24h`, `at &gt; now` and `0 &lt;= now - at &lt; 24h`.
- round2.md holds them once each, in its verifier's `ACCEPTED &lt;digest&gt; unit`.
- round3.md holds no escape.

**One slip, kept as written.** round2.md says four of six GU7 mutants were killed. Its own log (the verifier's `check\mut2.log`, read by the lead) holds four GU7 mutants, all killed, and 13 of its 14 mutants killed in all, as its summary says.

**What was changed after that, and nothing else:** a home path would be redacted as `<repos>`, `<scratch>` or `<home>`, as P0's and P0.1's reviews are (rule 3), and every other string the privacy gate reads as a home path as `<a home path>`. round1.md held none. round2.md and round3.md each held two, in their last lines: the verifier's scratch folder, redacted as `<scratch>`, and its sandbox folder, as `<home>`. None held any other string the gate reads as a home path.

| file | report | collected | its source's SHA-256 | home paths redacted | other strings redacted as `<a home path>` |
|---|---|---|---|---|---|
| [round1.md](round1.md) | P5.1's first verifier, on the full bar: NOT READY, on one code defect, a pre-flight record dated ahead of now taken by S7(c) (D1) | 2026-11-08 | `ec5c795c…` | 0 | 0 |
| [round2.md](round2.md) | P5.1's second verifier, on the full bar: NOT READY, on one prose defect, round 2's mutant tally promised by docs/P5.md and not given; every code ruling held | 2026-11-09 | `433fe7bd…` | 2 | 0 |
| [round3.md](round3.md) | P5.1's third verifier, on the ruled passage and what round 3 moved: READY, with no defect; round 2's 20 mutants killed again, on a baseline that passed first | 2026-11-09 | `b053fc44…` | 2 | 0 |
