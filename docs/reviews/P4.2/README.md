# P4.2's verifier reports

Each report as its verifier returned it, collected on the date its row gives. P4.2 takes what P4 left at its merge: the seventh verifier's false sentence and its closure of a test stand-in, A08, the fifth verifier's six findings about what the code does (C1 to C6), the teardown guard, and prose and test gaps. docs/VALIDATION.md's entry "P4 committed; P4.2 merged: what P4 left at its merge" says what it is and what each round found.

**Where each came from:** the verifier's final message, which the harness delivered to the lead inside a task notification; the lead read it out of its own transcript. The whitespace around it is stripped, and it is written ending in one line feed. The second verifier sent short messages after its report, as the last two stages of its run finished: round2-followup.md is the one that reports the run's end, taken the same way. The one before it reported one of those stages alone, and the four after it repeat it. No file holds an escaped `<`, `>` or `&`.

**What was changed after that, and nothing else:** a home path is redacted as `<repos>`, `<scratch>` or `<home>`, as P0's and P0.1's reviews are (rule 3), and every other string the privacy gate reads as a home path as `<a home path>`. Each home path is a place its verifier worked:
- its notes in the lead's scratch, as `<scratch>`;
- the start of its sandbox directory, or of a file in the temporary folder, as `<home>`.

round2-followup.md held none, and no file held another string.

| file | report | collected | its source's SHA-256 | home paths redacted | other strings redacted as `<a home path>` |
|---|---|---|---|---|---|
| [round1.md](round1.md) | P4.2's first verifier, on the full bar: NOT READY, on a gate and a sentence: the spy that holds C1 read no path given by keyword and saw no name bound before it went in, and limit 24 said two false things | 2026-10-31 | `01e9bfc1…` | 2 | 0 |
| [round2.md](round2.md) | P4.2's second verifier, on the full bar: READY; notes below the bar | 2026-11-07 | `8f0debb1…` | 2 | 0 |
| [round2-followup.md](round2-followup.md) | its follow-up, when its run's last stage finished: 22 stages passed and 2 skipped by name, the verdict unchanged | 2026-11-07 | `f1fe0635…` | 0 | 0 |
