# Study QRO-0's verifier reports

Each report as its verifier returned it, one file a draft, so that the study's section 15 cites them in this repository and not in a session's scratch space. Collected 2026-10-14.

**What was changed, and nothing else.** P0's verifiers, rounds 2 and 3, compared each copy with its source (R2-8, R3-4). Each change is stated here, and counted per file below:
- **A task notification's wrapper is removed** where a report arrived in one: the tags `<note>`, `<output-file>`, `<result>`, `<status>`, `<summary>`, `<task-id>`, `<task-notification>`, `<tool-use-id>`, `<usage>`, and what they carry, around the report. The report inside is kept whole.
- **A final line feed is added** where a report ended without one: so in each copy whose wrapper was removed.
- **CRLF line ends are made LF** where a source had them.
- **A home path is redacted** as `<scratch>`, `<repos>`, `<home-config>` or `<home>` (rule 3).

**Kept as received:** the transport that carried the reports wrote `<`, `>` and `&` as `&lt;`, `&gt;` and `&amp;`. No report holds a raw `<` or `>`; the wrappers, removed, held them. So a report's `&lt;` stands for its verifier's `<`.

| file | report | its source's SHA-256 | wrapper removed | final line feed added | CRLF lines made LF | home paths redacted |
|---|---|---|---|---|---|---|
| [draft01-verifier.md](draft01-verifier.md) | draft 1's verifier, delivered in session | `ad68431c…` | no | no | 0 | 1 |
| [draft02-recheck.md](draft02-recheck.md) | draft 2's re-check | `9ee16ee3…` | yes | yes | 291 | 1 |
| [draft03-recheck.md](draft03-recheck.md) | draft 3's re-check | `cd704d3d…` | yes | yes | 395 | 0 |
| [draft04-recheck-transcribed.md](draft04-recheck-transcribed.md) | draft 4's re-check, as the lead transcribed it into draft 5's packet; draft 5's verifier found it faithful | `15f8726d…` | no | no | 0 | 0 |
| [draft05-recheck.md](draft05-recheck.md) | draft 5's re-check | `721c9e7d…` | yes | yes | 226 | 1 |
| [draft06-recheck.md](draft06-recheck.md) | draft 6's re-check | `e341626a…` | yes | yes | 202 | 1 |
| [draft07-recheck.md](draft07-recheck.md) | draft 7's re-check | `fb03be39…` | yes | yes | 270 | 0 |
| [draft08-recheck.md](draft08-recheck.md) | draft 8's re-check | `5c8b6a4a…` | yes | yes | 172 | 1 |
| [draft09-recheck.md](draft09-recheck.md) | draft 9's re-check | `bbed9568…` | yes | yes | 131 | 1 |
| [draft10-recheck.md](draft10-recheck.md) | draft 10's re-check | `4c462915…` | no | no | 0 | 0 |
| [draft11-recheck.md](draft11-recheck.md) | draft 11's re-check | `23e658f6…` | no | no | 0 | 0 |
| [draft12-recheck.md](draft12-recheck.md) | draft 12's re-check: READY | `b3cd0bf2…` | no | no | 0 | 1 |
