# P0.8's verifier reports

Each report as its verifier returned it, collected on the date its row gives. P0.8 is the lead's piece for the owner's machine, which since a day between 2026-10-26 and 2026-10-30 opens no dangling junction; docs/VALIDATION.md's entries from "P0.8: this machine's dangling junctions" say what it is and what each round found.

**Where each came from:** the verifier's final message, which the harness delivered to the lead inside a task notification; the lead read it out of its own transcript. The whitespace around it is stripped, and it is written ending in one line feed. The notification carried a verifier's `<`, `>` and `&` escaped, and each file holds them as it carried them: round1.md `&lt;` three times and `&gt;` three times, for its verifier's placeholders `<crate>` and `<uuid>` and `dir`'s `<JUNCTION>`; round2.md `&lt;` four times and `&gt;` six times, for its placeholders and two arrows, `->`; round3.md `&lt;` and `&gt;` once each, for `<uuid>`; round4.md `&lt;` eight times, `&gt;` nine times and `&amp;` once, for its placeholders, `>=3.12`, and an `&` among the odd names it tried; round5.md `&lt;` twice, for a heredoc's `<<`.

**What was changed after that, and nothing else:** a home path is redacted as `<repos>`, `<scratch>` or `<home>`, as P0's and P0.1's reviews are (rule 3), and every other string the privacy gate reads as a home path as `<a home path>`. Each report held the places its verifier worked: the real repository's or moth-quantum's, as `<repos>`; its notes in the lead's scratch, as `<scratch>`; and the start of its sandbox directory, as `<home>`. None held another string the gate reads as one.

| file | report | collected | its source's SHA-256 | home paths redacted | other strings redacted as `<a home path>` |
|---|---|---|---|---|---|
| [round1.md](round1.md) | P0.8's first verifier, on the full bar: NOT READY, the checker failing on this machine, exit 3, on a crate holding a dangling junction; the entry's sentences on it false; the stranded `garbage-*` folders mostly P0's own tests' | 2026-10-30 | `0fa2367c…` | 5 | 0 |
| [round2.md](round2.md) | P0.8's second verifier, on the full bar: NOT READY, on one sentence, FORMAT.md item 12's "cannot open" wider than the code | 2026-10-30 | `ec89dda4…` | 3 | 0 |
| [round3.md](round3.md) | P0.8's third verifier, on the full bar: NOT READY, on two sentences, "cannot stat" still wider than the code, and the wrong-case corner; the cap reached | 2026-10-30 | `0132602e…` | 4 | 0 |
| [round4.md](round4.md) | P0.8's fourth verifier, on the relaxed bar: NOT READY, on one defect in what the code does, latent here: on Python 3.14 the question's answers rested on pathlib raising what it no longer raises | 2026-10-31 | `668170a3…` | 3 | 0 |
| [round5.md](round5.md) | P0.8's fifth verifier, on the relaxed bar: READY; two findings about the code below the bar, and notes | 2026-10-31 | `9eacd43e…` | 3 | 0 |
