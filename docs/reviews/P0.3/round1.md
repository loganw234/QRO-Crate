# P0.3 verifier, round 1: NOT READY

**Verdict.** NOT READY. I found one defect. It is a prose slip, and the code, the gates and the table are right. Everything else I tried held.

## Defect

**D1 (prose): the study's section 9.2 still says "four", where the amended section 10 says "three".**
- READ: `docs/studies/QRO-0.md` lines 1541-1543 say "which stages ran: crate-only, and any of section 10's four that need more. The anchor re-fetch is among those four".
- READ: section 10 at line 1738 now says "Three checks that need more than the crate". The lead removed the exact-hold bullet there.
- READ: `qro/vocabulary.py:411` and `docs/VOCABULARY.md:233` already say "any of the three".
- MEASURED: both study gates accept the frozen tree. The gates do not check this kind of count.
- MEASURED: on a copy, changing "four" to "three" in both places (lines 1541-1543) keeps `check_study.py` and `check_study_plants.py` at ACCEPTED, with the plants at 68 faults refused and 6 right variants accepted.

## What held

Everything below is MEASURED unless marked otherwise. Scripts and logs are in `SCRATCH\verifier-P03-r1\check\`.

- **Freeze.**
  - `SHA256SUMS.txt` begins `5dd8527bcf03956d`.
  - `sha256sum -c` over the tree gives 250 of 250 OK, with the same file set. The frozen tree was still unchanged at the end.
  - METHOD.md matches `pr-method.md`.
  - P0.2's packet hash begins `c459136c`, as the ledger says.
- **Runner, full.** `QRO_MOTH_ROOT=… bash verify/run.sh` in my copy (git-init'd, no commit) gave 17 passed, 7 skipped by name, 0 failed, in 147 s. The lead measured 133 s. My run was beside P0.2's verifier, so both timings are noisy.
- **Runner, quick.** `--budget quick` gave 14 passed and 4 skipped by name (p1, p2, p4, profile). Stage times sum to 74 s.
- **Ledger figures.** All of them reproduce:
  - tests: docs 134, tool-tests 102, vocab-tests 10, format 674, custody 23, control-tests 32; the 975 total is 14 more than P0.2's 961;
  - controls: 9 of 9 with 21 pending;
  - study plants: 68 and 6;
  - privacy: 250 files and 0 commit messages;
  - privacy controls: 37 of 37;
  - instruments: 5 of 5;
  - check-docs: 10 documents, 32 other markdown files and 35 source files;
  - the twin: `21fafec5…`;
  - the negative control: `raw-digest`.
- **Table against the designs.** `atk_table.py` parses the ledger's own tables and compares them with `V.TERMS` field by field.
  - It covers P1 item 7's 15 new rows and its 9 changed rows, and P2 item 10's 19 rows.
  - All six word sets, the 9 new types, owners and steps match, with 0 differences.
  - The two widened refusal meanings equal P2's text. The `context` row matches D10.
  - `Profile` and `version` are owner P0, as D1 decided.
- **Table against the reader.**
  - P1's own `vocab_check.py`, run on the P0.3 tree without patching and with the two profile entities added, accepts its 22-entity design graph. `atk_p2.py` does the same for a stand-in graph of P2's shapes and checks 17 faults.
  - One expectation changed: `version` on a `SoftwareApplication` is now `graph-form`, where P1's design measured `field-kind`. That follows from adding the term.
- **Reader's profile rule.**
  - About 60 hostile shapes (`atk_reader.py`, `atk_lists.py`) and 30,000 fuzzed crates (`atk_fuzz3.py`) gave 0 crashes. They included a list-valued version, a reversed `@type` order, a right `@id` not typed `Profile`, an extra `Profile` entity, odd versions, the order against other step-1 checks, and a 980-deep or 1 MB version value.
  - The reader agreed with an oracle I wrote from D1 and D10, except where an earlier generic check refuses first.
  - The CLI, run as a process, gives exit 1 with a single escaped REFUSED line.
- **No vacuous P0 test.** I patched `_profiles` to raise a distinct exception. Over 739 tests, only the 8 new profile cases reached it. No older test now passes for the wrong reason.
- **Goldens.** `atk_golden.py` re-derives `twin-body.json` and the identity `21fafec5…` with `json` and `hashlib` alone, and a fresh fixture equals `twin-metadata.json`. The custody and audit goldens are byte-identical to P0.2's, and they never held the twin's identity.
- **`spelling`.** `atk_spelling_diff.py` compared P0.2's and P0.3's `problem()` over 474,110 values across 12 spellings, with 0 differences. Patterns, writers and helpers are equal. `PATTERNS` holds the module's own objects, and `problem()` reads them for all 8.
- **Stand-in parcels.** I overlaid a P4 (`tools/gen_profile.py`, `tests/p4`), a P1.1 (`register_p1`, `tests/p1`), and a P2 (`register_p2`, `tests/p2`, `tests/p2crates`), plus `tests/p1crates` and `tests/p4shacl`.
  - The runner passed on the combined copy: 23 passed, 0 failed, and p4-shacl skipped by name until I added its directory.
  - p1-crates, p2-crates and p4-shacl skip by name without their variable and run with it.
  - None of them is in the quick budget, and `profile` is.
  - With `register_p1` and `register_p2` loaded, the format, controls, twin and custody stages still pass.
  - `misnamed` flags wrong prefixes in lettered directories such as `tests/p2crates` and `tests/p4shacl`.
  - A docs page without its index line fails check-docs, and an index line without its page fails.
- **Hand mutants.** `mutate.py` ran 25 mutants of P0.3's code and registry. 15 were killed. Three are equivalent in behaviour: `R-held-by-id-set` (same refusal name and place), `F-profile-entities-unsorted` (the writer sorts), and `G-count-of-parcel-guards` (a message only). Seven survived and show the test gaps in the Notes below, one of them a table change that the `vocabulary` stage catches but pytest does not.

## Notes

Test reach (code right):
1. **Reader order.** Only "profiles before mentions" is pinned. Moving `_profiles` after the dangling-reference check, or before the root `conformsTo` check, survives all 674 format tests. So does raising `context` for any entity whose version differs, even when its name or keys also differ. The shipped code returns `graph-form` there, as D10 says.
2. **`misnamed`'s new `[a-z]*`.** No test uses a lettered parcel directory. Reverting to `p[0-9]+` leaves the docs stage at 134 passed.
3. **The new `need_env` guards.** `guard_problems` reads only `need_file`. Deleting `need_env QRO_MOTH_ROOT` before p1-crates, or retargeting p4-shacl's to the wrong variable, survives. A mistyped variable would skip a stage by name forever. The existing `instruments` guard has the same gap.

Gate reach:
4. **Naming rule.** `sanity()` refuses `qro:Pub` against `qro:PUB`. It does not refuse a term and a type with the same key, such as `qro:Pub` as both, which share an anchor on the page. No row does this today, because types are capitalised and terms are not required to be lowercase.
5. **`--resume` fingerprint.** It covers the moth-quantum checkout but not `QRO_SHACL_PYTHON`, so a cached p4-shacl pass can be reused under a different engine.

Prose:
6. **Study section 10.** It still says the law "is not re-derived" and that the checker "checks the sum, the digest and the support". The dated entry in section 17 says step 6 also simulates the law circuit. The lead chose a note over an in-place edit, but the compile row and the "four checks" line were edited in place. Whether this counts as false is arguable, so I left it as a note.
7. **Extra `Profile` entity.** The reader refuses it with `graph-form` ("a Profile entity for no profile the root conformsTo"). A test covers it, but FORMAT.md item 21, the `graph-form` row and the ledger entry do not say so.
8. **FORMAT.md item 19.** It still says "the golden bytes do not move", though three twin goldens were regenerated. D1 said FORMAT.md would say so.
9. **Forward tense.** "which P4's shapes read" appears in `spelling.py:39-41`, the FORMAT.md table row, and the `descriptor()` docstring. It is true only once P4 lands.
10. **Study amendment.** "Its measured cost per gate list was 1.3 s" is P2's single reading, on a loaded machine, for the law gate list. Its own 12 distinct gate lists took 33 s in all, nearer 2 s each.
11. **Registry docstring.** `tests/docs/test_stage_registry.py` lines 33-35 still say a guarded stage "runs the directory it guards". The function docstring covers the tool case.

For the P1.1 and P4 briefs:
12. P1's design relied on `version` on a `SoftwareApplication` being `field-kind`; it is now `graph-form`. For a `field-kind` example, FORMAT.md's stated limit names `agent`, which I confirmed is still `field-kind`.
13. The lead's old `sim_parallel.py` plants `qro:commitment` on the raw result, which the table now refuses.

P0.2's part:
14. I found no fault in it. P0.2's frozen tree holds `__pycache__` dated 19:57:11, in `controls/` and `qro/`. I loaded only its `spelling.py`, with bytecode writing off, so I believe another process made them (BELIEVED). I left them alone.

## What I did not do

- I ran no real P1, P2 or P4 code, since none exists. I used stand-ins only.
- I did not re-run the lead's mutants or harness.
- I fetched no URL, so what GitHub or w3id.org resolves is BELIEVED.
- I did not test `--resume`, a POSIX host, the privacy gate over commit history (my copy has no commit), or the SHACL engine.
- I touched no key, token, CRN, `.atlas` directory or credential file, and I did not connect to IBM or Atlas. The instruments stage read moth-quantum read-only.
- **Rule slip.** Some of my scripts made scratch crates in the OS temp directory, and I used `/tmp/readme.bak` and two `/tmp` file lists. I removed all of them. pytest's own `tmp_path` use by the repo's tests wrote to its usual place.
