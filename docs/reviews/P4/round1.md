# P4, round 1: verifier report

**Verdict: NOT READY.**

P4's shapes claim more than the checker holds, in two ways, on crates P4 did not pick. A real engine fails must shapes on crates the checker accepts (defect 1). Where a must shape fails, the checker often refuses by a name the shape's claims do not hold (defect 2). There is also a wrong exit code (defect 3). The Profile Crate does not meet a MUST of RO-Crate 1.3 although three places say it holds what 1.3 asks (defect 4). Several statements in the tree are false or incomplete (defect 5). A few gates cannot fail (defect 6). This is round 1, so I applied the full bar. Everything else I attacked held, and I list it at the end.

All runs were in my copy, `SCRATCH\verifier-P4-r1\check\p4`. The freeze checked out: the tree matches SHA256SUMS.txt (298 files, `bfec37ab444d38cc`), and P4's worktree has the same 298 files. My scripts are in `check\scripts\`. The engine ran as P4's stage runs it: its interpreter, `-I`, P4's runner with the guard first.

## Defects

### 1. A must shape fails on a crate the checker accepts (code)

This is the design's central property, first half.

- **Fully accepted crates (MEASURED, `probe3.py`).** I registered a generator under the fixture's generator name, so `checker.check` accepts each of four crates at all nine steps, step 9 included.
  - Two CreativeWorks with ids `#a` and `./#a`, each with a `name`. P4's evaluator and pyshacl both fail `term-name`.
  - The same with `schema:a` and `http://schema.org/a`. Both fail `term-name`.
  - A CreativeWork with id `_:b0`. pyshacl fails `entity`; the evaluator abstains.
  - A top-level File `@x` that has a `name`. pyshacl fails `term-name`; the evaluator conforms, because it reads `file:///crate/@x` while rdflib reads the root's IRI.
- **P4's own plants (MEASURED, `probe4.py`).** `edge-blank-node-id` and `edge-absolute-file-id` are accepted through step 8. pyshacl fails `entity` and `file-digest-present` on them. `profile/EXAMPLES.md` prints "none fail" for both. The engine stage leaves all four "abstains" plants out of its corpus; `test_p4shacl_crates.py` asserts the omission.
- **Breadth (MEASURED, `idshapes.py`).** I added one CreativeWork under each of 1,516 ids. The checker holds 1,513 through step 8.
  - pyshacl fails a must shape on 79 of them: 41 `term-name` and 38 `entity`.
  - The 41 are ids that rdflib reads as the root's IRI: `.`, `././`, `//` and every `@`-leading id.
  - The 38 are `_:` ids.
  - rdflib raises `Invalid IPv6 URL` on 2 (`//[$`).
- **Where the expansion and rdflib part (MEASURED, `idgrammar.py`, `pathfuzz.py`, `idfuzz.py`).**
  - About 96,000 ids generated from the expansion's own grammar all resolve as rdflib resolves them.
  - Every id starting with `@` differs. That includes valid file paths: 51 of 5,000 sampled.
  - FORMAT.md item 11 permits `@` in a path.
  - So the claim that the expansion "refuses what rdflib would not resolve the same way" is false.
- **Why no gate sees it.** The soundness gate, both fuzzes and the accepted-plant walk skip every crate the expansion refuses.
- **Exposure today.** P0's own generator is unaffected: 34 odd file names, `@x` among them, all conform in both layers (MEASURED, `filenames.py`). A failure needs two entities sharing a single-valued term, or a blank-node or `file:` id.
- **Cause.** The reader admits any printable-ASCII id with no space. RDF cannot tell `_:b0` from "no `@id`", and cannot see that two spellings are one IRI. Part of the fix is in the reader (P0's). P4 alone could loosen `entity`'s node kind and the `file:` test, but then `entity-no-id` and the digest rule weaken.

### 2. A must shape fails where the checker refuses by a name its claims do not hold (code)

This is the central property, second half. The shape-fails-so-checker-refuses half holds here; the name does not.

- **Sweep (MEASURED, `singleedits.py`).** Of 12,591 single edits of the fixture, none has a must shape failing while steps 1 to 3 accept. In 202 edits, in 21 classes, the checker's first refusal is not in the union of the failing shapes' claims.
- **Realistic ones (MEASURED, `probe5.py`).**

| Edit | Checker names | Shape fails | Shape claims |
|---|---|---|---|
| A second name spelt `schema:name` on the root | `term-unknown` | `term-name` | `spelling` |
| `schema:sha256` on a CreativeWork | `term-unknown` | `domain-sha256`, `file-reached` | `graph-form`, `file-unlisted` |
| `license: []` | `spelling` | `root` | `graph-form` |
| A File renamed in its own entity only | `graph-form` | `file-reached` | `file-unlisted` |
| `hasPart` written as one object | `spelling` | `file-reached` | `file-unlisted` |

- **Alias keys (MEASURED, `aliaskeys.py`).** 65 of 124 crates built by giving every term an alias key (a compact or absolute IRI) show the mismatch. This is the largest class, about 140 of the 202. `LIMITS` 5 mentions alias keys only as a looseness.
- **The text it contradicts.** `profile/README.md` says "when a shape fails, the checker refuses by one of those names". `docs/P4.md` and every `qs:claims` say the same.
- **Clearing it.** Widen the claims, which are true if widened, or restate the sentence for single-fault crates with no alias keys or empty lists. `test_every_claim_is_a_refusal_the_table_names_...` pins today's claims.

### 3. `tools/gen_profile.py --check` exits 3 on a corrupted Profile Crate (code)

- **Fault (MEASURED, `exit3.sh`).** Set one entity's `@id` in `profile/ro-crate-metadata.json` to a list or an object. The tool prints the drift, then "the generator itself failed, TypeError: unhashable type: 'list'", and exits 3. The contract is exit 1: drift, or a Profile Crate that fails its check.
- **Fuzz (`pcfuzz.py`).** 2,724 of 20,000 edited Profile Crates make `check_profile_crate` raise: `p4_profile.py` lines 434, 482 and 516.
- **Impact.** The `profile` stage fails either way. The wrong code hides the verdict.

### 4. The Profile Crate does not hold what RO-Crate 1.3 asks, and three places say it does (prose, with a content cause)

- **What the specification says (READ, the profiles page and its source, through WebFetch's extraction).**
  - An entity representing a JSON-LD context "MUST have an absolute URI as `@id`", retrievable as JSON-LD.
  - Extension terms SHOULD be mapped in the Profile Crate's `@context`.
  - A `hasArtifact` target SHOULD declare `encodingFormat`.
- **What the crate has (MEASURED).**
  - `context.jsonld` has the relative `@id` `context.jsonld`.
  - The crate's `@context` is the single RO-Crate URL, with no mapping of the `DefinedTerm`s.
  - `#hasVocabulary` and `#hasShapes` point at entities with no `encodingFormat`.
- **Where the claim stands.** "Holds what RO-Crate 1.3 asks" is in `docs/P4.md:36` and `:86`, `tools/gen_profile.py:18` and the stage text at `verify/run.sh:353` (the lead's). `check_profile_crate` reads none of these three.
- **Clearing it.** Restate the claim or state them as limits. Limit 17 states only the media type.

### 5. Other false or incomplete statements (prose)

- **Limit 19 and its echoes.** "The shapes say nothing of the crate" is false for a real engine (defect 1). It appears in `profile/README.md:78`, `docs/P4.md:144`, `qro/p4_expand.py:14`, `qro/p4_profile.py:135` and `qro/p4_examples.py:483`.
- **Limit 4.** It says an absolute IRI other than `file:` is exempt, as the checker exempts it. Change 1 of the seven (the `file:`-only digest rule) therefore leaves an absolute `file:` File stricter than the checker, and neither limit 4 nor limit 19 says so correctly.
- **Limit 5.** It omits the failures alias keys cause (defect 2).
- **Limit 1 and the README.** Both say tests hold the property "over every crate plant any parcel registers that its control row says is accepted". That walk examines 0 crates today (MEASURED: `examined == 0`). The only built accepted plant is a custody log.
- **`p4_expand.py` docstring and `docs/P4.md:54`.** They say it refuses what rdflib would not resolve the same way. That is false for `@`-leading ids.
- **`EXAMPLES.md` rows.** "None fail" for two of the "abstains" plants is false for pyshacl (defect 1).

### 6. Gates that pass a fault they claim to catch (gate)

- **The published-date test.** I replaced the constant `DATE_PUBLISHED` with the clock, regenerated, and ran the p4 stage. It passed (MEASURED, my mutant P01). `test_the_published_date_is_one_constant_and_not_the_clock` accepts any date from 2026-10-16 on, which is today. From the next day the committed file drifts and the `profile` stage fails, so the fault surfaces late but loudly.
- **Two vacuous assertions.**
  - `assert examined &gt;= 0` at `test_p4_examples.py:303`.
  - `... or True` at `test_p4_tool.py:126`, which was meant to hold that `--write` writes nothing when the context is missing. The code does behave that way: `render` raises before any write.

## Notes (below the bar)

- **The seven changes.** Changes 2 to 7 are fine and stated. Change 1 is a loosening toward the checker, allowed but incomplete (defect 5). It was not escalated, although the brief asks that design changes be.
- **Limit 3 is incomplete.**
  - It omits the trailing line feed for `binary64` and `iri` (MEASURED, `spellprobe.py`). No term uses those spellings today.
  - By the SHACL Recommendation a pattern is a SPARQL REGEX, where I believe `$` does not match before a final line feed (BELIEVED, not re-read). pyshacl and the evaluator are both looser than that.
- **SHACL layer.** Evaluator and pyshacl agree on 3,350 random graphs over the real shapes. The only differences are how a literal focus node is named, because rdflib normalises `"+1"` to `"1"`. That is not a SHACL difference.
- **The guard.** It replaces four calls. `gethostbyname`, `getfqdn` and UDP `sendto` are allowed (MEASURED on loopback, `guardgap.py`). Nothing in pyshacl or rdflib uses them, so there is no leak. "Blocks the network" is looser than the four calls the same sentence lists.
- **Stale docstring counts.** `test_p4_spelling.py` says 140 samples and `test_p4shacl_probe.py` says 280; there are 288.
- **Empty directory.** An empty directory under `profile/` is not noticed by `--check`, though `--write` removes it. Git cannot commit one.
- **README wording.** "Published 2026-10-16" asserts a publication that has not happened. The date is a placeholder the lead sets.
- **Timings.** Beside P1.1, the quick budget took 1 m 33 s and the whole runner 3 m 32 s. CLAUDE.md says about 70 s and about 125 s.
- **`p4_expand` docstring.** It says "non-negative integer", but the code accepts any integer; the shapes hold the bounds.
- **Trailing vacuous assert.** `assert X.NOTES` ends `test_p4_shapes.py` and cannot fail.

## What held

- **Whole runner (MEASURED).** `QRO_MOTH_ROOT=… QRO_SHACL_PYTHON=… bash verify/run.sh`: 20 passed, 0 failed, 4 skipped by name (p1, p2, p1-crates, p2-crates), 3 m 32 s.
  - p4: 681 tests in 21 s.
  - profile: under 1 s.
  - p4-shacl: 199 tests, 35 to 46 s.
- **Quick budget (MEASURED).** `--budget quick`: 16 passed, 2 skipped, 1 m 33 s.
- **Stability.** Test order does not matter (reversed and two shuffles). Line coverage of P4's modules by the p4 stage is 1,629 of 1,636 lines.
- **Generator.**
  - Six environments (hash seeds, TZ, locale, cwd) render identical bytes, equal to the committed profile.
  - Exit codes 0, 1, 2, 3 and the stated 120 on a closed pipe behave as documented in 16 experiments, except defect 3.
- **Files and environment.**
  - The requirements file is byte-identical to the lead's (SHA-256 `254a5577…8b95`).
  - The engine environment holds exactly the eight wheels and pip, and my runs changed nothing in it.
  - The stage fails loudly without the variable, with a wrong path, and with an interpreter that lacks pyshacl.
  - The Python in the engine stage is run with `-I`; the guard precedes the pyshacl import.
- **Whose files.** Against 7f40400 the only changed file is `docs/README.md`: two lines, at the end of the list. Everything else is P4's own, and nothing in the checker's path imports P4's modules.
- **Renderer.** I decompiled the committed Turtle with rdflib and compared it with the model: 139 of 139 shapes equal, field by field (`dump_model.py`, `decompile_engine.py`).
- **Text spelling.** Over all 1,114,112 code points the shape is never stricter than the checker; it is looser only for controls, surrogates and a trailing line feed.
- **Crash fuzz.** 60,000 random JSON inputs into the expansion and evaluator produced no crash.
- **Mutation.** I re-ran 24 of P4's mutants: 16 quick-stage mutants (15 killed, and E35 survives as P4 says) and 8 engine-runner mutants (all killed). I ran 23 of my own, aimed at the gates: 22 killed, and the date mutant survived.

## What I did not do

- I did not run rocrate-validator, any other SHACL engine, or fetch GitHub pages (anchor behaviour, raw MIME type).
- I did not build any P1, P2 or P3 plant; none is built. The accepted-plant walk is untested on real plants.
- I re-ran 24 of P4's 283 mutants, not all of them, and did not re-run its 8,000-seed fuzz.
- I ran only on this Windows host.
- I did not read `p4_cases.py` or the bodies of the eval, expand, turtle and model tests line by line.
- My sweeps are samples, not proofs.
- The XPath reading of `$` and JSON-LD 1.1's handling of keyword-like ids are BELIEVED, not re-read.
- I touched nothing in `frozen\`, the worktrees, the ledger, P4's scratch or the engine environment. I removed four small files I had left in `/tmp`.
