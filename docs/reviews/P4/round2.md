# P4, round 2: verifier report

**Verdict: NOT READY.** This is P4's second round, so the full bar applies.

Round 1's fixes hold, and no must shape ever failed on a crate the checker accepts. The second half of the central property still fails. Three families of crates, each one edit from an accepted crate, make a must shape fail where the checker refuses by a name no failing shape claims. The pool behind P4's sweeps never makes these edits, so no gate sees them. The sentence stating the property is therefore false in eight places.

The freeze checked out (MEASURED, `sha256sum -c`): 344 files OK, `SHA256SUMS.txt` begins `3b1ffc677e22a1db`, and the four ledger/brief/report copies match. My copy is `SCRATCH\verifier-P4-r2\check\p4`. Scripts are in `<scratch>\verifier-P4-r2\check\scripts\`.

Clean full-runner run (MEASURED): `QRO_MOTH_ROOT=… QRO_SHACL_PYTHON=… bash verify/run.sh` gave run `20261026-040740-35563-c8c3cfe+dirty`. 21 stages passed, 0 failed, and p2, p1-crates and p2-crates skipped by name. p4 had 822 tests, p4-shacl 215 and p1 1,169. The quick-budget stages summed to 198 s on this shared machine.

## Defects

### 1. [code] A must shape fails where the checker refuses by a name its claims do not hold

This is the same class as round 1's defect 2. Round 1 added `spelling` and `term-unknown` to every must shape's claims and called them "the two refusals of form that can come first". Three more come first, and RDF cannot show them or shows them differently. All three are single edits of the fixture, and the evaluator and pyshacl agree on each.

**(a) `graph-form`: an @id twice, a case clash, a file and a directory.**
- RDF merges nodes by IRI, so an added entity's single-valued term becomes a second value.
- Fault: add `{"@id":"data/notes.txt","@type":"File","contentSize":"999"}` to the fixture. The checker refuses `graph-form` (an @id twice). `term-contentsize` fails, and its claims are `spelling, term-unknown`.
- Likewise `{"@id":"./","@type":"Dataset","name":"another root name"}` fails `term-name`.
- `{"@id":"data/NOTES.txt","@type":"File"}` (a case clash) and `{"@id":"data","@type":"File"}` (file and directory) fail `file-digest-present`. Its claims are `file-digest, raw-digest, spelling, term-unknown`.
- MEASURED (`e5_dupid.py fixture|atlas`, `f4_dupid.py`): 12 of 378 duplicate-id additions to the fixture are unclaimed, in 9 classes. For the Atlas-shaped crate it is 36 of 882, in 19 classes.
- This answers your question about other shapes failing where the checker refuses `graph-form`. 46 of the 131 must shapes lack `graph-form`: the 45 term shapes of non-reference terms, and `file-digest-present`.

**(b) `context`: an edited top-level `@context`.**
- The runner keeps a crate's inline context (`ctx[1:]`), as a real tool would.
- Fault: set `@context` to `[&lt;RO-Crate 1.3 URL&gt;, {"qro": &lt;namespace&gt;, "name": "http://example.org/n"}]`. The checker refuses `context`. pyshacl fails `entity`, `profile-entities` and `root`, and none of those claims `context`.
- Redefining `hasPart` fails `entity`, `file-reached` and `root`. Redefining `sha256` fails `entity` and `file-digest-present`. Redefining `File` fails five shapes. Pointing `qro` elsewhere fails `entity` and `root`.
- Only `profile-version` claims `context`.
- The evaluator abstains on these crates, and no engine-stage test reads one.
- MEASURED (`f2_context.py`): 6 of 8 variants fail a must shape.
- A top-level `@reverse` has the same shape of fault: the checker says `graph-form`, pyshacl fails `term-name` (`f3_toplevel.py`).
- Limit 19 calls an abstained crate "harmless". That holds for ids, where `spelling` is claimed. It does not hold here.

**(c) `file-missing`: an added File entity with no file on disk.**
- Fault: add `{"@id":"x.txt","@type":"File"}`, listed or not. `python -m qro check --fixtures` says `REFUSED file-missing at x.txt`, exit 1. `file-digest-present` fails.
- With a sha256 and size but not listed, `file-reached` fails. A raw result with no `qro:rawForm` fails `rawresult-form`. None claims `file-missing`.
- MEASURED (`f1_filemissing.py`, `e3_additions.py`): of 320 additions, 28 are unclaimed, in 3 classes.
- The same shows in P1's crates when a File entity is copied to a new path. That is 22 of 24,286 edits and 22 of 23,902 on the IBM-shaped crate, and 2 of 10,879 on the Atlas-shaped one.
- This is the nearest to a "several faults" reading, since the entity also lacks a digest. But the added entity is one edit, and the checker's name for it is `file-missing`.

I could not test `file-link` because the host cannot make a link. I believe it is in the same class, from reading `checker.walk` (BELIEVED).

Clearing it: either widen `FORM` by `graph-form`, `context`, `file-missing` and `file-link`, or restate the sentence for crates with one entity per @id, the reader's `@context` and every listed file present.

I tried the widening in a scratch copy (`check\alt\p4`, MEASURED):
- My additions, duplicate-id, context and top-level probes show no unclaimed name.
- `tests/p4` passes 818 of 822. The 4 failures are the tests that pin today's claims, including `test_p4_refs`'s pin that no other term claims `graph-form`. So you choose how.

### 2. [gate] Nothing in the quick or engine stage can see these faults

- The sweeps' pool is the first verifier's plus `MORE` (`tests/p4/p4_sweeps.py`). It deletes, sets, retypes and renames existing entities, but never adds an entity under an existing id or adds a File.
- It never edits the top-level `@context`. The 124 alias-key crates add only a fresh `#alias-host`.
- The engine-stage corpus has no changed-context crate.
- So the sweeps' zero is true of the edits they make, and says nothing about these.

### 3. [prose] The property sentence is false in eight places

The false sentences are "every must shape adds the two refusals of form that can come first" and "a crate one fault from an accepted one is refused by a name a failing shape claims". They stand in:
- `profile/README.md`: the intro and the requirement-levels row (limit 1 is scoped to its samples and is true as scoped).
- The banner of each shape file under `profile/validator/qro-crate/`.
- `docs/P4.md`: lines 7–13 and 85–87.
- `qro/p4_shapes.py`: lines 10–17 and the `FORM` comment at 60–66.
- `qro/p4_model.py`: the `Shape.claims` docstring.
- `qro/p4_examples.py`: lines 4–8.
- `qro/p4_profile.py`: lines 77–85, 212, 385–390 and 403.

They clear with defect 1.

## Round 1's fixes and the rulings

- **Defect 2.** Re-run on the current tree:
  - `singleedits.py` (12,591 edits): A 0, B 0.
  - `aliaskeys.py` (124 crates): 0 unclaimed, and the engine equals the evaluator.
  - `probe5.py`: its six cases are claimed.
  - All 1,088 edits the expansion cannot read are refused at steps 1 to 3.
- **Defect 3.** About two dozen process runs of `gen_profile.py` (`gen_exit.sh`):
  - Misshapen or missing Profile Crates, an unexpected file, an empty directory, CRLF, a non-ASCII byte and a missing context all exit 1.
  - Bad arguments exit 2, and a closed pipe exits 120. None exits 3.
  - Nine renders (3 hash seeds × 3 time zones) were identical and equal to the files on disk.
- **Defect 4.** I read the Profile Crate against RO-Crate 1.3's profiles page. Its extraction by WebFetch is READ.
  - Root typed `Dataset` and `Profile`, description `File` about the root, contextual `Profile` entities, `encodingFormat` on every artifact, and the context entity at an absolute IRI with `application/ld+json`.
  - The gaps are stated as limits 9, 11, 17 and 22.
  - The committed fixture copy is accepted with `--fixtures` and refused `step-unbuilt` without it.
- **Defect 5.** The old false sentences are gone from P4's files. Limits 1, 4, 5 and 19 are true as scoped.
  - Limit 19's second-base claim holds: at `https://example.org/crate/` an absolute twin of `data/notes.txt` fails `term-name` in both readers while the checker accepts (`e7_base.py`).
- **Defect 6.**
  - A clock-derived `DATE_PUBLISHED` is killed by `test_no_file_of_p4_reads_a_clock`; by reading, another test also requires the constant to be a string literal.
  - `examined == crates` and the former `or True` are real assertions.
  - Of 342 test functions, none lacks an assert or a raises.
- **Defect 1, P4's part.**
  - Probe3's four crates can no longer be built, because the reader refuses their ids. Probe4's `abstains` plants behave as the matrix says.
  - Five gate mutants of mine were killed: the unread-crate skip in the soundness gate, the fuzz, the sweep and the accepted-plant walk, plus the name check.
  - The engine-stage ids test passed in the full runs.
- **Graph-form claim on the 18 `ref` terms.** The claim is true in P4's 288-crate test, which passes in my runs. It is not the only gap: see defect 1(a).
- **Plant renames and P0.4/P0.5 changes.** The `abstains-*` and `compact-id-entity` plants are consistent with the code and the matrix. The only stale mention of the old `edge-*` names is the lead's `docs/VALIDATION.md:2500`.

## Soundness and the evaluator against the engine

- **A = 0** (a must shape fails while steps 1 to 3 accept) in every family I tried:
  - 59,067 single edits of P1's synthetic crates, accepted through P1's built steps 4, 5 and 8 (`e1_p1crates.py`, `e2_p1edits.py`);
  - 320 added-entity crates, and 1,260 duplicate-id additions across the fixture and the Atlas crate (`e5_dupid.py`).
- **Evaluator and pyshacl agree** on triples and on failing (shape, focus, severity) for 4,350 edited crates P4 never sampled (`e4_diff.py`): 0 differences.
- **Random shapes over random graphs** (`e6_shapefuzz.py`, 28,000 cases, pyshacl through P4's runner): 18 disagreements, of two kinds.
  - `sh:minLength 0` on a blank node: the evaluator fails it and pyshacl does not (16 cases). By the Recommendation the evaluator is right (READ, WebFetch's extraction of 4.4.1).
  - `sh:maxInclusive` alone against a boolean literal: the evaluator fails it and pyshacl passes it (2 cases). I believe the evaluator is right, from SPARQL's comparison rules (BELIEVED, not re-read).
  - The generated shapes use neither construct: min_length is only 1 and bounds always come in pairs.

## Notes (below the bar)

- **Test reach, code right.** With `-I` dropped from `run_engine` and the guard moved after the pyshacl and rdflib imports, the guard, environment and probe tests all pass. All three tests are in `tests/p4shacl/`. The code is right today. Docstrings and `docs/P4.md` say "before anything else is imported"; `hashlib`, `json`, `sys` and `socket` come first.
- **Requirements file and engine stage.**
  - The file is byte-identical to the lead's copy at `SCRATCH\p4\shacl\` (`cmp`; I read no other file there).
  - With the variable unset, wrong, or pointing at an interpreter without pyshacl, 3 of 5 environment tests fail loudly.
  - With the variable unset, the runner skips p4-shacl by name.
- **Lead's merge-time items.**
  - `verify/run.sh:369` still reads "holds what RO-Crate 1.3 asks", and the p4-shacl text lacks the clause you ruled.
  - CLAUDE.md's "about 70 s" for the quick budget is far from 198 s here, on a noisy machine.
- **Order and robustness.**
  - `tests/p4` passes in reversed and shuffled order (822 passed); `tests/p4shacl` passes reversed (215 passed).
  - 40,000 random inputs into the expansion and evaluator gave 0 crashes.
- **Whose files.**
  - Against 37640f0 the only changed file is `docs/README.md` (the two index lines at the list's end).
  - The rest is 7 `qro/p4_*.py`, `tools/gen_profile.py`, `profile/`, `docs/P4.md`, `tests/p4/` and `tests/p4shacl/`.
  - The stages leave no stray files.

## What I did not do

- I did not run rocrate-validator, a second SHACL engine, or P0.6's gate.
- I did not re-run P4's 434 mutants. I ran 5 gate mutants, 3 runner/date mutants and the widened-`FORM` experiment.
- I did not test `file-link` or symlinks, or any host but Windows.
- I did not read every test body, or the SHACL Recommendation and RO-Crate pages in full. Both came through WebFetch extractions.
- My sweeps are samples.
- My first runner launch overlapped a second (my mistake). The numbers above are from the clean third launch.
- I touched nothing in `frozen\`, the worktrees, the ledger, P4's scratch or the engine environment. In P4's scratch I only grepped one sweep file.
