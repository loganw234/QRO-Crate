**Verdict: NOT READY.** I found no defect in what the code does, and no gate that passes a fault it claims to catch. Two sentences in the tree are false. Both are prose, and the code beside them is right.

Scripts are in `SCRATCH\verifier-P05-r3\check\mine\` unless named. "Engine" is the shacl-venv's python with `-I`, rdflib 7.6.0 on Python 3.12.9. "py313" is `py -3.13 -I`, which also has rdflib 7.6.0. The brief says 3.13.5 has no rdflib. It does: the install dates from 2026-05-21.

## Freeze and runner
- The brief begins `ef2ddcc4175dedd4`, and SHA256SUMS.txt begins `bd761b115c0d46b8`. `sha256sum -c ../SHA256SUMS.txt` in `frozen\tree` gave 263 OK with the same file set (MEASURED). The 13 changed files and `docs/reviews/P0.5/` are byte-identical to the real repository's working tree (MEASURED, `cmp`).
- `QRO_MOTH_ROOT=<repos>/moth-quantum bash verify/run.sh`, in a `git init` copy, gave 17 passed, 0 failed, 7 skipped by name, exit 0, and 151 s of stage time (MEASURED).
  - Counts: docs 164, tool-tests 129, vocab-tests 12, format 838, custody 23, control-tests 32, which is 1,198.
  - The twin is ACCEPTED `21fafec5…`.
  - The +14 over round 2 are all in `test_spelling.py` (225 to 239 tests, `pytest --collect-only`).
- The lead's 39 mutants, re-run with `check_ids.py` then `hm_t.py` on a clean copy, were all killed by their targets (MEASURED).
- P0.4's own tests against the new code: 5 fail and 714 pass. The five are the intended ones (MEASURED).

## Defects

### D1 (prose). Item 22 names RFC 3986 where JSON-LD 1.1 is what was measured
- FORMAT.md lines 272 and 276 say "distinct `@id`s name distinct IRIs, as RFC 3986 resolves them" and "each was read as RFC 3986 reads it, and no two the same". VALIDATION.md line 2706 says "read each as RFC 3986 does".
- For an absolute id this is false. RFC 3986 section 5.2.2 sets `T.path = remove_dot_segments(R.path)` when the reference has a scheme (READ, via WebFetch).
- The fault that shows it:
  - `http://example.org/a/../b` and `http://example.org/b` are both accepted (`id_problem`).
  - RFC 3986's algorithm gives `http://example.org/b` for both (MEASURED, `rfc_mine.resolve`, which I held to the RFC's section 5.4 examples).
  - rdflib and JSON-LD 1.1 keep an absolute IRI as written, so they are two nodes (JSON-LD 1.1 API step 6.2, READ via WebFetch; MEASURED in `claims_probe.py`).
- In the lead's own `p05\r2fix\jobs9.json`, 131,262 of the 300,000 ids are absolute.
  - RFC 3986 section 5.2.2 changes 9,531 of them.
  - 325 target IRIs are shared by two or more of them (MEASURED, inline script).
  - Example: `ftp:p/../` and `ftp:.w/../` both give `ftp:/`.
  - The lead's `compare9.log` compares against "JSON-LD 1.1", not RFC 3986. The comparator was right and the sentence names the wrong one.
- A fix would say: "as JSON-LD 1.1 reads them: a relative id by RFC 3986's basic algorithm, an absolute IRI as written".

### D2 (prose, test comments). Two sentences false in the way round 2's D3 was
- (a) `test_spelling.py` lines 360–361 say "No accepted id ends in #".
  - `ab:#`, `ab:x#` and `urn:x#` are accepted. `ab:#` is in the same file's accepted list.
  - 32 of the 11,667 ids in the test's own draw end in `#` (MEASURED, `draw_stats.py ../ptree`).
  - What is true is "no accepted relative id". VALIDATION.md's "no accepted id reaches that clause" is true.
- (b) `test_hostile.py` lines 189–190 and VALIDATION.md lines 2516–2517 say a refused path is refused first by the id rule for "a character no @id holds".
  - `%`, `:`, `#`, `*` and `?` are held by fragment and absolute ids, for instance `#a%41`.
  - `data/a%b.txt` and its kind are refused because the whole string is in none of the four forms.
  - Round 2's D3 fixed the same slip at line 424 but not this sibling.

## What held (code)
- **rdflib against the rule, Context.resolve, rdflib 7.6.0.** Engine and py313 gave identical readings at every base. Each run was checked against my own RFC 3986 resolver (MEASURED, `gen_ids.py`, `rdf_run.py`).

  | Id set | Bases | Ids | Result |
  |---|---|---|---|
  | my random draw | 24 | 739,634 | 24 per-base digests equal across the two Pythons; no blank node, vanished node or exception; no merge but limit 1 |
  | exhaustive small alphabets (`gen_exh.py`) | 8 | 761,204 | no deviation |
  | every `;` id over `a . ; /` to length 11 (`semi_exhaust.py`) | 4 | 1,550,488 | urljoin changes none |
  | real `Graph.parse`, subject and object position | 8 | 90,018 | same as above |

  - The 24-base run deviates from RFC 3986 only at the empty-path base `https://example.org`, where 274,321 fragments read as `https://example.org/.#a`. That is a `normpath('')` quirk, with no merge. Round 2's note 5 already named it, and item 22 does not state it.
  - The merges in the first run are limit-1 pairs only. An absolute id equals a relative id's resolution there, as item 22 says.
  - A further 60,018 ids at 12 odd bases (params, query and dot or empty segments in the base) show base-path quirks, again with no merge beyond limit 1.
  - The `;` rule is right: no accepted last segment is changed.
  - `x;` is split at ten base schemes (http, https, ftp, sftp, imap, shttp, mms, prospero, rtsp, rtspu). Item 22 names three. That is under-inclusive, not false, and the rule is base-independent (MEASURED, `params_bases.py`).
- **urllib.** On 739,634 ids, `urlsplit`, `urlparse`, `urldefrag` and `urljoin` at five bases raise on none, under 3.12.9 and 3.13.5 (MEASURED, `urllib_raise.py`). `.port` raises on 658, such as `a+b://a:b&amp;`. That is limit 2's class, and no node IRI reaches it in rdflib's code (READ: only `_iri2uri`, for fetched locations).
- **The spec.** Reading the IRI expansion steps (6.1, 6.2, 6.4, 6.5, 8; READ, via WebFetch) shows every accepted id is read as the checker means it. A fragment holding `://` is returned unresolved by the spec as well.
- **Prefixes.** `CONTEXT_PREFIXES` is exactly the 23 names rdflib expands, which are 22 simple terms ending in a gen-delim plus `qro`. `name:x` and `schema://x` stay themselves. This holds in both the list and merged-dict context forms, on both Pythons (MEASURED, `prefix_probe.py`).
  - It matches JSON-LD 1.1 section 4.2.2 step 14.5 (READ).
  - The pinned context is byte-identical to the live RO-Crate 1.3 context today (MEASURED, `curl` and sha256: `5a3df1a4…21dd91`).
- **Every prose reading is true** (MEASURED, `claims_probe.py`, `notoffered_probe.py`). That covers all ids FORMAT.md item 22, the `spelling.py` comment and the "not offered" docstring say rdflib reads in a stated way, at `file:///crate/` and `https://example.org/crate/` through a real parse. The 18 "reads as written" ids are each read as spelled.
- **Narrowing.** This round's rule accepts nothing round 2's refused: 0 widenings in 2,350,646 strings (`widen_check.py`).
- **Serialisers.** nt, turtle, n3, xml, pretty-xml, json-ld, trig and hext round-trip 4,018 accepted ids losslessly (`serial_check.py`). trix did not finish, so I stopped it. longturtle and nquads errors were my harness's.
- **pyshacl 0.40.1.** A node shape of mine (one IRI node and one `schema:name` per CreativeWork) conforms on 18,000 accepted ids at five bases, one node per id (MEASURED, `shacl_check.py`). The controls (the P4 pair `#a` with `./#a`, `schema:0` with `http://schema.org/0`, `_:b0`) do fail, so the harness can see merges.
- **References, item 22's two names.** 209,883 ids were used as the root's `license`, as a `hasPart` reference and as a new entity's id. `graph-form` and `spelling` come out as item 22 says (`spelling` at `@graph[i] @id` for entities), with 0 disagreements and 0 crashes (MEASURED, `refs_experiment.py ../ptree 250000 2`). One apparent disagreement was my own duplicate `hasPart` value.
- **Code against prose.** The code matches my independent reading of item 22 on 2,350,646 strings (`ref_rule.py`) and on 1,602,555 one-change neighbours of 617 other seeds (`neighbours.py`). The sweep's `an_id` matches my reading on 1,071,452 strings (`sweep_vs_prose.py`).
- **Crash and time.** 400,014 fuzz calls over Unicode and non-str inputs gave 0 crashes. The worst case, a 2 MB id, took 0.92 s, with no ReDoS.
- **Command line.** 291 ids, as an entity and as a reference (582 crates), were run through the CLI of the 20d40e6 tree and the frozen tree. Every exit was 0 or 1, one REFUSED line each, no traceback, nothing newly accepted (MEASURED, `cli_diff.py ../oldtree ../ptree 260 7`).
- **Review README.** The source SHA-256s `83500274…` and `89349f29…` match, the redaction counts 2 and 1 match, the escapes are present, and the files end in one LF. The CRLF set is unchanged, 8 files.

## Gate
- **The model against rdflib.** `rdflib_reads` equals `Context.resolve` on 17,751,216 readings (739,634 ids × 24 bases) on both Pythons, with 0 differences (MEASURED, `model_vs_rdflib_mine.py`). On 78 readings of the control test's shapes, the model also equals rdflib (`control_vs_rdflib.py`).
- **The test's resolver.** The test's `rfc3986` equals mine on every relative id at every non-urn base.
- **The restored assertion.** `p05\assert_check.py` rerun: with a leading `./` let through, the property test fails with the assertion and passes without it.
- **The draw.** It gives 11,667 accepted ids, with 335 and 672 refused against the threshold of 300.
- **The test file under 3.13.5.** Through a pytest stub, `test_spelling.py` (238 of 239 tests) and `test_sweep.py` (26) pass under 3.13.5 and 3.12.9. The one skipped needs a fixture (`run_tests_313.py`).

## Notes (code right; test reach, prose, other)
1. **Compact-IRI tails.** I made 23 mutants of my own. Twenty were killed. Two real ones survive every stage and the format, vocabulary, custody, controls, docs and tools directories (MEASURED, `hm_t.py ... m_p05... m_r3.py`):
   - A rule that refuses a compact IRI only when its tail begins with a letter, which accepts `schema:0`.
   - A rule that refuses one only when the tail holds no `#`, which accepts `schema:a#b`.
   - rdflib expands `schema:0`, `rdf:_1` and `schema:a#b` (MEASURED, `prefix_tail.py`).
   - With the first mutant, the whole reader accepted a crate whose entities `http://schema.org/0` and `schema:0` are one node in rdflib. The frozen reader refuses it (`mutant3_demo.py`).
   - The third survivor, a space admitted in `_ID`, is an equivalent mutant: the later patterns still refuse a space.
   - The gate is `prefix + ":x"` and a few examples.
2. **The `@` rule.** A rule that refuses `@` unless a digit follows, `(?!@(?![0-9]))`, passes all 905 tests in format, vocabulary, custody and controls. rdflib reads `@0` and `@9/y` as the root. Natural mutants were killed: `(?!@[a-z])` by the sweep, and `(?!@[A-Za-z])` by the bare `@` example and the sweep. The sweep disclaims reach beyond one change from its seeds.
3. **The property test's model is `norm_url` alone.** It omits `Context.expand`: compact IRIs, `@`-first, `_:` and spaces. That is why note 1 and note 2 pass. The `rdflib_reads` docstring's first sentence ("the IRI rdflib's JSON-LD reader makes of an @id") reaches wider than the model does. For accepted ids it is exact.
4. **The 3.13.5 claim in item 22 is true but its provenance is not.** I ran rdflib 7.6.0 under both Pythons. The lead's brief says none is installed under 3.13.5, so its 3.13.5 figure can only have been the model's. "MEASURED" reaches past that.
5. **Bases outside the nine.** Item 22's general sentence ("distinct @ids name distinct IRIs") reads wider than its nine bases. It is false at bases urllib does not join (`mailto:`, `s3:`, where relative ids vanish; round 2 note 5), and for the empty-path base above. Not collisions. The "Not taken" ledger line is the only place this is stated.
6. **Round 2's tightening was never re-checked against other parcels.** The ledger's P1.1 checks (entry 1's search, entry 2's 1,018 tests) predate round 2's brackets, bare `%` and second `#`. Entry 3 has no P1.1 line. A fragment id such as `#qubit[0]` is now refused. I could not look at the parcels' trees.
7. **"So that an IRI has one spelling."** `%2f` beside `%2F`, `%41` beside `A`, and host case remain several accepted spellings. RDF and JSON-LD compare IRIs as strings, so there is no merge.
8. **Item 22 and `spelling.py` do not carry the `;` rule's scope sentence.** They name only "an http, https or ftp base", which is true but not the whole set (see the `;` bullet above).
9. **The draw's thresholds** leave about 11% margin on the `://` count. A change to the draw fails loudly, not silently.
10. **Housekeeping.** I wrote four small list files to the system temp early on and deleted them. The project's pytest runs, including the runner and mutants, use the system temp as theirs do.

## What I did not do
- I did not read P1.1's tree, the parcels' worktrees or the ledger. "P1.1's 1,018 tests pass" and "writes none of the refused forms" are unchecked.
- I ran no JSON-LD processor other than rdflib 7.6.0. Specification claims are READ through WebFetch's extraction (a small model's quotes). I did not run Python 3.14 or another rdflib version.
- P4's shapes and the p4-shacl stage are not in this tree. The SHACL runs used my own shape.
- I did not verify the lead's 226 s timing, "546,297 draws", or the privacy counts "5 commit messages and 13 staged versions". My copy has one commit.
- My id sets are bounded by alphabet and length, plus random draws, so longer ids are covered only by those.
- I did not run `--budget quick` separately. It is a subset of the full run.

Files: `SCRATCH\verifier-P05-r3\check\mine\` (scripts and logs), `check\work\tree` (runner copy), `check\ptree` (clean import copy), `check\mut_mine.log`, `check\mut_lead_rerun.log`.
