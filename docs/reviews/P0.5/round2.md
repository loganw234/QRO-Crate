**Verdict: NOT READY, on prose only.** I found no defect in what the code does and no gate that passes a fault it claims to catch. Three sentences in the tree are false (D1 to D3). Restating them is what stands between this tree and READY.

## Freeze and runner

- The frozen SHA256SUMS.txt begins `65bddf982d5acf14` and the brief begins `27986f9b8bd3d701`. `sha256sum -c` over `tree\` gave 262 of 262 OK, with the same file set (MEASURED).
- I ran everything in a `git init` copy, `check\work`. `QRO_MOTH_ROOT=<repos>/moth-quantum bash verify/run.sh` gave 17 passed, 0 failed, 7 skipped by name, exit 0 (MEASURED).
  - Test counts: docs 164, tool-tests 129, vocab-tests 12, format 824, custody 23, control-tests 32, which is 1,184 and matches the ledger.
  - The twin is ACCEPTED `21fafec5…`.
  - Stage time was 195 s on a shared machine.
- 20d40e6's own tests run against the new code: 5 of 719 fail. They are the `qro:RawResult` id cases, the `%` path case, the old `ref` class example and the old sweep statement, all intended (MEASURED).

## Defects

**D1 (prose). "The rest rdflib reads as written" is false.**
- The sentence appears in FORMAT.md line 249 and in qro/spelling.py line 43.
- The docstring of `test_an_id_in_a_form_the_rule_does_not_offer_is_refused` (test_spelling.py line 200) adds "or, holding a space, the string as written".
- A space: `Context.resolve('a b')` returns `""` and `Graph.parse` makes no node, so the entity vanishes. This holds at `file:///crate/` and `https://example.org/crate/`. The two space cases are the only members of the docstring's 15 ids that rdflib does not read as written (MEASURED, `mine\few.py`, `claims_probe.py`).
- A query with nothing after it: `a?` reads as `file:///crate/a`, the IRI of the accepted id `a`. `?` reads as the root.
- Other refused forms are also read otherwise: `/x` reads as `file:///x`, `//x` as `file://x/.`, and `../a` as `file:///a` (MEASURED, `few.py`).
- Of the 103,828 refused strings in a 19-character alphabet to length 4, about 1,475 grammatical ones are in none of item 22's families and not read as written (`rest_probe2.py`). 1,444 of those hold an empty query.
- The refusals stand. The sentences should say "most of the rest", name these, and say a space makes no node.

**D2 (prose, stated limit). Limit 1 is narrower than the class it concedes.**
- FORMAT.md line 262 says "an absolute IRI that names a path of the crate". A fault outside that wording passes every gate.
  - Both ids are accepted. At a crate read at its descriptor's URL, `#a` and `https://example.org/crate/ro-crate-metadata.json#a` are one node with two names.
  - `#a` with `https://example.org/crate/#a` at `https://example.org/crate/`, and `#a` with `urn:example:crate/#a` at a urn base, do the same (MEASURED, real `Graph.parse`, `mine\limit1_fault.py`).
  - The draw never puts an absolute id under a base (test_spelling.py line 300).
- Restate the limit as the class: an absolute IRI equal to the IRI some relative id resolves to where the crate is read, a path, the root or a fragment.

**D3 (prose, trivial). A false test comment.**
- test_hostile.py line 410 says "since P0.5, % is no @id's". Fragment ids and absolute ids hold `%`, and `#a%20b` is in the accepted list of test_spelling.py. It should say "no path's".

## Notes (below the bar)

1. **Gate, test reach.** The round-1 rewrite of `test_distinct_ids_resolve_to_distinct_iris` dropped the old assertion "each relative id is its IRI with the base removed". That assertion saw `./x` and `a/./b` one id at a time.
   - With a leading `./` admitted, the old test fails at once on `./hS/EVx)d`. The new test stays green (MEASURED, both trees, `loosen_tb.py`).
   - Three other tests (the unit list, the sweep and `test_two_entities…`) still fail on it, so no fault passes the stage.
   - I loosened the id rule in process one class at a time, 30 classes. Every class fails at least one test. The property test alone fails on 19 of them. The other 11 are held by the unit tests or the sweep only.
   - Four of those 11 are rdflib-relevant: a leading `./`, a `file:` IRI, a compact IRI and `_:`. Four others are held by the sweep alone (`*`, `\`, `[`/`]` in a path, a one-character scheme), and rdflib reads them as written.
   - Re-adding the one assertion for relative path ids would close the gap.
2. **Gate, model fidelity.** `rdflib_reads` leaves out the last clause of `norm_url`, which puts back a trailing `#`. For `#` at `file:///crate/` the model gives `file:///crate/` and rdflib gives `file:///crate/#`.
   - It is exact on every accepted id: 0 differences in 17,848,837 readings of my own at 47 bases, and 0 of the lead's 5,100,000 re-run on their saved outputs. Their 3.12 and 3.13 model outputs are byte-identical.
   - The omission can only make the gate fail wrongly, never pass wrongly. The "empty fragment admitted" loosening is caught by the model's error, not by an rdflib collision.
3. **Test reach.** `PATHS_REFUSED_AS_IDS` (test_hostile.py line 184) is computed from the code under test. The first assertion of `test_every_refused_path_is_refused_by_one_rule_or_the_other` (line 199) is a tautology. The sweep and the rule tests hold the id rule, not these.
4. **Limit 2 understates (prose).**
   - Accepted absolute ids such as `ab://[` make `urllib.parse.urlsplit` raise ValueError. That breaks `URIRef.defrag` and rdflib's RDF/XML parser when it is given a base.
   - The JSON-LD parse and pyshacl (4 modes) are unaffected (MEASURED, `xml_probe.py`, `shacl_ill.py`).
   - Conformant JSON-LD→RDF drops a node whose IRI is not well-formed (READ, API 8.1 and 8.2).
   - Refusing `%` without two hex digits, `[` and `]`, and a second `#` is cheap. That is the lead's call.
5. **Missing qualifiers.** FORMAT.md's measured claim does not name the Python.
   - The readings are identical under 3.12.9 and 3.13.5 at 46 bases (MEASURED, `norm_probe.py` digests). 3.14 was not run.
   - At bases urllib does not join (`s3:`, `git+https:`, `data:`, `mailto:`, `tag:`), rdflib leaves every relative id relative and the parser drops the node. That is 123,669 of 266,401 ids, the root among them. It is rdflib's quirk, not the rule's.
   - Other exotic bases make rdflib depart from RFC 3986 on every id alike, with no merge at any. Examples are a base with no path, where `#a` reads as `https://example.org/.#a`, an empty query, and dot or empty segments in the base.
6. **Prose ambiguity.** Item 22's "last segment" is undefined for a directory path. The code takes the text after the final `/`, so `x;/` is accepted. The spelling.py comment (line 47) attaches "which begins .; or ..;" ambiguously to "path" or "last segment".
7. **Pre-existing, not P0.5's.** `canonical.write` raises TypeError, not Refused, on a non-string `@id`. It does so at 20d40e6 too (MEASURED, `writer_ids.py`).
8. CLAUDE.md's "~125 s" is stale: I measured 195 s of stage time. This is already P0.6's.

## What held (MEASURED)

- **The rule against rdflib 7.6.0.** I enumerated 799,200 accepted ids exhaustively: paths over `a . / ;` to length 9, fragments, and 20 schemes of absolute ids. `Context.resolve` gave RFC 3986's reading at every hierarchical base, with no merge, blank node, exception or vanished node (`diff_probe.py`).
  - There are 17,848,837 readings at 47 bases, including `file:` with a drive, the descriptor's URL, `;params` in the base, a query, ports, userinfo, ipv6 and urn.
  - A real `Graph.parse` of all the ids at four bases, in subject and object position, gave 0 blank nodes, 0 vanished nodes, 0 merges and 0 disagreements with `Context.resolve` (`parse_probe.py`).
  - The `;` rule is right. No accepted last segment is changed by urljoin.
- **`CONTEXT_PREFIXES`.** It is the 22 simple terms whose IRI ends in a gen-delim plus `qro`, by JSON-LD 1.1's rule (READ, API 4.2.2 step 14.5) and by rdflib's rule. Both give the same 23, and the pinned context has no expanded definitions (`ctx_prefixes2.py`).
- **References.** FORMAT.md item 22's two names hold on 58,639 trial references, with 0 disagreements (`refs_check.py`).
- **Lead's figures.**
  - Round 1's 400,000 ids: the new rule refuses exactly the 7,617 that deviated (6,242 fragments and 1,375 last segments).
  - The sweep's statement `an_id` agrees with the code on 2,522,831 strings.
  - The lead's 30 mutants are all killed by a real test failure on my re-run, including the one that failed to compile.
  - The draw gives 11,695 ids with 346 and 630 refused, the same under 3.12 and 3.13.
- **Old against new reader.** On 20,000 random id edits of the fixture there is no widening, 106 narrowings, 2,912 graph-form to spelling, 1,341 spelling with a new `where`, and no crash in either tree. The CLI exits 1 with one REFUSED line on awkward ids, including control characters, a lone surrogate and a 100,000-character id.
- **Prose figures.** The review README's hash and redaction counts, the test-count arithmetic, item 11's `readme:hidden` limit and the CRLF set all check out.
- **Serialisers.** nt, turtle, json-ld, n3, trig and hext round-tripped 6,917 ids losslessly.
- **ReDoS.** There is none: 800,000-character ids take under 80 ms.

## What I did not do

- I did not read P1.1's tree, the worktrees or the ledger, so "P1.1's 1,018 tests pass" and "P1.1 writes none of the refused forms" are unchecked.
- P4's shapes and the p4-shacl stage are not in this tree. The SHACL runs used my own small shapes.
- No JSON-LD processor other than rdflib 7.6.0 was run. The specification claims are READ through WebFetch's extraction (a small model's quotes). No Python 3.14, no other rdflib version.
- I did not compare the live RO-Crate 1.3 context with the pinned copy, and did not run `--budget quick`.
- My id sets are bounded by alphabet and length. Longer ids are covered only by the lead's random draws, which I re-ran.
- I wrote two small file lists to `/tmp` early on and deleted them. The project's own pytest runs used the system temp directory.

My scripts are in `SCRATCH\verifier-P05-r2\check\mine\` and `…\probe\`. Each docstring gives its command line, and the engine ones run as `…\shacl-venv\Scripts\python.exe -I &lt;script&gt;`.
