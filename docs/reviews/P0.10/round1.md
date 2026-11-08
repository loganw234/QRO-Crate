**Verdict: READY.** I found no defect that meets the NOT READY bar. I did not run mutants of my own, and I read the tests rather than breaking them (see the end).

## Defects

None, in code, gate or prose.

## What I checked

**Freeze and packet**
- The SHA256SUMS prefix is `90a6c197704830d3` and all 520 files check out (MEASURED, `sha256sum -c`).
- `diff -rq` against main shows exactly the 31 paths of the brief: 3 added, 28 changed. Nothing of P1's or P2's moved.
- All changed files are LF and ASCII. The non-ASCII counts in four files equal main's (MEASURED, byte counts).

**Generated files**
- `gen_vocabulary.py --write` and `gen_profile.py --write`, run through sbx.sh on a copy, reproduce VOCABULARY.md, REFUSALS.md, CONTROLS.md, context.jsonld and the whole of profile/ byte for byte (MEASURED).

**Rows (READ against P3.md items 5 and 11 and P5.md item 12)**
- Types, the six terms (kind, spelling, many, absent words, owner, domain), all word sets and their order, `route`, and `comparison-generated` are as designed. No term is CHECKED.
- The eighteen `statement` sentences equal item 5's table.
- The registry texts of `single-runs`, `readout-unbounded` and `time-confounded` equal their sentences. `not-interleaved` quotes the `device-and-time` sentence.
- The builder's kit meanings say what P5 items 5, 6 and 10 refuse. `once-only` says "a submission" where S1 also says "a line holding any commitment"; I judge that no more or less than the rule.
- `audit-stage` gaining `comparison` makes "any of the four" true.

**`python -m qro compare` (MEASURED, sbx.sh)**
- **Misuse, exit 2:** zero or one argument; a bad or empty directory; a crate directory given twice. "Twice" is caught for case, a trailing separator, `\.`, `..`, forward slashes, an 8.3 short name and a junction.
  - A trailing dot or space is refused as "reads as another".
  - The `\\?\` prefix and `::$DATA` are refused as "no such crate directory".
- **Module missing:** one `REFUSED step-unbuilt at comparison` line, exit 1.
- **Module present, with a stand-in of the contract's shape:** the arguments pass in order. The results:
  - **Accepted line:** exit 0.
  - **`Refused`:** exit 1.
  - **`Misuse`:** exit 2.
  - **Other outcomes:** a crash, a summary that is no ACCEPTED line, `None`, a missing `check`, an import error and `SystemExit` or `KeyboardInterrupt` all give exit 3.
  - **Closed stdout, or a closed pipe:** exit 3, never 120.
- **Embedded newlines or escapes in a summary** are escaped on output, as for `check`.
- **`check` unchanged:** 18 argument shapes give the same code and text as on main, apart from the usage line.

**Stages (MEASURED, my own copy with the directories made)**
- **Variables unset:** `lint-kit`, `p3` and `p5` run and pass once their directories exist. `p3-crates`, `p5-kit` and `p5-crates` skip by name with their messages.
- **Variables set:** a failing `p5kit` test fails the stage, a skip inside a stage fails it, and a lint fault in `qro_kit` fails `lint-kit`.
- **Budgets:** `--list --budget quick` marks `lint-kit`, `p3` and `p5` only, and CLAUDE.md's list matches it.
- **Fingerprint:**
  - **`kit-env`:** `absent` while `QRO_KIT_PYTHON` is unset; otherwise the interpreter path plus a package hash, stable across runs.
  - **`--resume`:** with the variable unset it is refused as a changed environment. With the same value it resumes.
  - **`--require-all`:** a skip fails the run.
- **Ruff configuration walk:** the docs walk fails a `ruff.toml`, `.ruff.toml`, `RUFF.TOML` or `.RUFF.toml`, and a `pyproject.toml` with a `[tool.ruff]` table, in `qro_kit` or below it. It ignores a `pyproject.toml` without one.

**Controls' runner (MEASURED, with a stand-in plants module of my own)**
- **Plant raising `Refused`:** it is the outcome, judged by name. `controls.plant` writes it, exit 1.
- **`Compared`:** it is told before the custody branch and is `step-unbuilt` while the module is missing, both in `controls.run` and in `controls.plant`. With a stand-in it takes the stand-in's answer.
- **`states` row:** it is `states` only when the sentence is in the plant's set and the twin is accepted without it. The other outcomes:
  - Plant lacks the sentence: `accepted`.
  - Twin says it too: `twin-states`.
  - Twin refused: `twin-refused`.
  - STATEMENTS or TWINS entry missing: pending, not counted as built, and not WRONG.
  - STATEMENTS returning a string or a list: the run fails with exit 3.
- **Sentences:** all five `states` rows yield a sentence. The registry text of `single-runs`, `readout-unbounded` and `time-confounded`, and the quoted sentence of `not-interleaved`, equal their statement words. `unit-incomplete` yields its backticked label.
- **`joint-omission`:** it expects `comparison-generated`, with its text cell unchanged.
- **P4's walk:** it skips any tuple, as before.

**NOTICE.md**
- It names 56 files under tests/p1/data/moth. The breakdown is 18 + 12 + 12 + 12 + 1 + LICENSE, and I counted the same (MEASURED). The licence line matches the LICENSE file.

**P4's figures**
- The changes are figures only: the counts, the clash list, and the fuzz's draws (800 to 1500). They are arithmetically consistent: 6 × (1+69) + 4 = 424, 2 × 68 = 136, 420 / 3 = 140.
- The full runner passes p4 and p4-shacl.

**Runs**
- My full runner on the packet, run 20261108-084250-58607-f3aea8d: 24 passed, 0 failed, 6 skipped by name (`lint-kit`, `p3`, `p5`, `p3-crates`, `p5-kit`, `p5-crates`). No other stage skipped.
- The lead's run, as you reported it, gives the same tally.
- My `kit-env` line matches the builder's f5 line: `…kit-venv/Scripts/python.exe 389cb3dcb47dcb2f`. The sitecustomize change is invisible to it, as you said. That is a stated limit of the fingerprint, not a defect.

**Junctions**
- The new tests, run under pytest with `--basetemp` inside my directory, left none: 749 entries scanned, 0 links.

## Notes

All of these are below the bar.

- **Prose, `qro/__main__.py` and FORMAT.md item 23:** "the command and the control cannot answer differently" is overstated. `qro.__main__.compare` skips the directory and duplicate-crate misuse rules, which live in `_main`. A `Compared` plant naming a crate directory twice would exit 2 under `controls.plant` but reach the module under `controls.run`. Valid plants answer alike.
- **Prose, P4 comments the grant left:** stale old figures remain in comments and docstrings. Examples are `tests/p4shacl/test_p4shacl_sweeps.py` ("1,088", "124 alias-key crates"), `tests/p4/p4_sweeps.py`, `qro/p4_shapes.py` and the "63 terms" in `test_p4_twin.py`. The lead already leaves docs/P4.md's historical figures for P4's notes piece.
- **Behaviour the design does not state:** a comparison directory given again as a crate directory is not misuse. It passes to P3's module. P3's step 1 ("a crate the declaration does not name") may cover it.
- **Test environment:** two closed-descriptor tests in `test_compare_cli.py` start bash and fail at low integrity (sbx.sh). They are not defects of the code, and 140 other tests passed there. The full runner, which runs them through sbx-mid, passed `format`.

## What I did not do

- I ran no mutants of my own. I relied on the builder's 38 and on tests that pass.
- I did not run the `p5-kit` stage against real kit tests, since tests/p5kit does not exist yet.
- I did not run the `\\?\` prefix against a real crate.
- I did not check the builder's slips beyond reading them. The builder's one stray empty file in `/tmp` is its own report, not something I verified.
- I did not check the live ledger, moth-quantum's contents or the builder's mutant transcripts.
- Since the IBM job ids under tests/p1/data/moth are never printed here, I did not scan the tree for ids that were not there before.
