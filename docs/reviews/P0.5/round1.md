**P0.5 round 1: verifier report. Verdict: NOT READY.**

I found two code defects: accepted `@id`s that rdflib 7.6.0 does not read as the IRI the checker means. The first is at P4's own base `file:///crate/`. The second is at any http, https or ftp base. Item 22's claim is false for both. I also found a gate that cannot see either defect and a set of false statements in the prose. Everything else I attacked held (listed below).

**Freeze and runner.**
- The frozen sums file hash begins `2c593be8afba62ec`. All 260 files matched at the start and at the end, and they equal the real repository's working tree (MEASURED: `sha256sum -c`, read only).
- In a `git init` copy, `QRO_MOTH_ROOT=<repos>/moth-quantum bash verify/run.sh` gave 17 passed, 7 skipped by name, 0 failed, exit 0, and 167 s of stage time (MEASURED).
- The twin is ACCEPTED `21fafec5…`. The tests total 1,129, against 1,038 at 20d40e6 (MEASURED: the old tree exported with `git archive`).
- My scripts are in `SCRATCH\verifier-P05-r1\check\probe\` and `check\mut\`. Each script's docstring gives its command line. `check\work` is a clean copy of the frozen tree.

## Defects

### 1. A fragment id holding `://` is not resolved against the base (code)

- **Fault.** `id_problem` accepts `#a://b`, `#a:b://c` and `#:://`, because a fragment may hold `:` and `/`.
- **What rdflib does.**
  - It returns any id containing `://` unchanged (READ: `rdflib/plugins/shared/jsonld/util.py:227`).
  - So the node is the relative IRI `#a://b`, not `file:///crate/#a://b`.
  - JSON-LD 1.1 does the same when the first colon is followed by `//` (READ via WebFetch's extraction: API 5.2.2 step 6.2).
  - It says an RDF conversion ignores a node whose IRI is relative or not well-formed (READ: API 8.1 and 8.2).
- **Rate (MEASURED).** Of 400,000 accepted ids over six bases, all 6,242 fragments holding `://` stay unresolved at every base, `file:///crate/` among them. The other 164,294 fragments, 192,258 absolute ids and 37,206 relative paths resolve as RFC 3986 says at that base. Of the 6,242, 576 are ones JSON-LD 1.1 itself would resolve, so rdflib deviates from the specification there too.
  - Commands: `gen_probe_ids2.py &lt;tree&gt; jobs_ctx2.json 400000 7`, `rdf_probe.py`, `compare.py`, `classify.py`.
- **Whole crate (MEASURED).** Crate B is the fixture plus a CreativeWork `#a://b`. The real checker accepts it at all nine steps (a generator that reproduces the file, as P4's verifier did), and rdflib at `file:///crate/` has the subject `#a://b`.
  - Commands: `demo_crates.py`, `rdf_crate.py`.
- **Why it is a defect.** It is the property item 22 states ("the graph the checker holds is the graph a JSON-LD reader makes"), at P4's base, in P4's engine. I saw no collision and could not run P4's shapes, so I did not show a must shape failing.
- **Fix tried, not applied.** `(?!.*://)` in `_FRAGMENT_ID`.

### 2. An id whose last segment ends in `;` is read as another id, or as the root, at an http, https or ftp base (code)

- **Fault.** `;` is a sub-delimiter that `_ID_SEGMENT` admits (item 11). So `x;`, `a/b;`, `;`, `.;` and `a/..;` are accepted.
- **Cause.**
  - rdflib resolves a relative id with Python's `urljoin` (`util.py:244`).
  - For a base scheme in `urllib.parse.uses_params` (http, https, ftp, sftp, tel and others), `urljoin` splits `;params` off the last segment and drops them when empty.
  - It also treats a `.` or `..` before the `;` as a dot segment.
  - `file` is not in that list. That is why P4's base and the lead's test do not show it (MEASURED with plain `urljoin`; the same quirk makes `;`, `.;` and `a/..;` read as the root at the urn base).
- **Rate (MEASURED).** At `https://example.org/crate/`, `http://example.org/a/b/` and `https://example.org/crate/x;p/`:
  - all 1,015 ids whose last segment ends in its first `;` differ from RFC 3986;
  - all 360 whose last segment is `.` or `..` followed by `;` differ too;
  - 103 to 105 nodes are made of more than one id;
  - one node, the root `https://example.org/crate/`, is made of 24 ids: `./`, `;`, `.;`, `a/..;`, and so on;
  - at `file:///crate/`, none.
  - Real `Graph.parse` in subject and object position agrees with `Context.resolve`.
- **Whole crates, accepted at all nine steps (MEASURED).**
  - Crate A has Files `data/notes.txt` and `data/notes.txt;`. At the https base they are one node with two `sha256` values.
  - Crate C has an entity with the id `;`. At the https base the root node has two `name` values.
  - A small pyshacl 0.40.1 shape of my own conforms at `file:///crate/` and fails at the https base on both crates. The shape says a file has one `sha256` and a Dataset one `name`. These are not P4's shapes.
  - This is P4's defect 1 (`@x` read as the root) again, with a different spelling and a different base.
  - Commands: `demo_crates.py`, `demo_root.py`, `rdf_crate.py`, `rdf_root.py`, `shacl_demo.py`.
- **The claim.** Item 22 says "So distinct `@id`s name distinct IRIs". Its one stated limit (an absolute IRI that is itself a path of the crate) does not cover this.
- **Fix tried, not applied.**
  - The change: no `;` in the last segment of an id that does not end in `/`.
  - With it and Defect 1's fix, 300,000 draws over six bases show 0 deviations from RFC 3986 and 0 merges. So these two shapes explain every deviation I found.
  - 779 of the 781 format and vocabulary tests still pass.
  - The two that change are the sweep's id statement and `test_a_name_of_every_character_the_alphabet_admits_is_held_end_to_end`.
  - The alternative is to state the limit and withdraw the claim.

### 3. The property test does not see Defect 1 or 2 (gate)

- **What the test does.** `test_distinct_ids_resolve_to_distinct_iris` models rdflib as `urljoin` against the one base, `file:///crate/`, where urllib agrees with RFC 3986 on `;`. It claims to hold "the property the rule is for".
- **The fault it passes (MEASURED, `prop_base.py`).** The test body, copied unchanged with only the base changed to `https://example.org/crate/`, fails on the first collision, `('32/lu/DpVbH;', 'https://example.org/crate/32/lu/DpVbH')`.
- **Defect 1.** The model resolves `#a://b`, which rdflib returns before it reaches `urljoin`.
- **The lead's own draws.** `gen_ids.py` and `probe_ids3.py` have the same limits. They found no `://` in about 6,700 short fragments, which is chance, not coverage.

### 4. False statements in the tree (prose, code right)

- **FORMAT.md item 22, "refused `spelling`, an entity's `@id` and a reference's alike".**
  - A reference whose id is not IRI-shaped is refused `graph-form` ("names no entity"). Examples: `_:b0`, `@x`, `.`, `//`, `./x`, `a//b`, `x#a`, `#`, `?q`, `C:/x`, `a b`.
  - The name is the same as at 20d40e6.
  - Only references that look like IRIs (`schema:a`, `file:a`, `HTTPS://x/y`) are `spelling`.
  - MEASURED: `refs_demo.py`.
- **Item 22, "since a JSON-LD reader reads it otherwise"; `qro/spelling.py:40`, "reads each other form otherwise"; and the docstring of `test_an_id_a_json_ld_reader_reads_otherwise_is_refused`.**
  - 13 of the 34 refused examples are read by rdflib as the IRI they spell, and none is a second spelling of an accepted id.
  - They are `@`, `x#a`, `data/#a`, `#`, `#a#b`, `?q`, `a?b`, `HTTPS://example.org/a`, `Https://example.org/a`, `file:a`, `C:/x`, `notes.txt:hidden`, `https://example.org/&lt;a&gt;`.
  - They are refused as forms the rule does not offer, which is harmless. The text should say so.
- **`qro/reader.py:61-67` (the `absolute()` docstring).**
  - It still says `README:hidden` "reads as an IRI".
  - It was accepted at 20d40e6. It is now refused `spelling` (MEASURED: `readme_hidden.py` on the old and new trees).
  - FORMAT.md item 11 was changed to `readme:hidden`; the docstring was not.
- **CLAUDE.md ("the one RDF reads") and the ledger entry ("the reader's part of that defect").** Both are as false as Defects 1 and 2 make item 22.

## What changes with another base (MEASURED)

| Base | Effect |
|---|---|
| `file:///crate/`, `file:///C:/crate/`, `file:///crate/sub/`, the cwd-derived `file:///C:/…/` | Defect 1 only. |
| `file:///crate` (no trailing slash) | Defect 1 only. `./` is `file:///` and `x` is `file:///x`. |
| `https://example.org/crate/`, `http://example.org/a/b/`, `ftp://…/`, `https://…/?q=1` | Defects 1 and 2. |
| `https://example.org/crate/ro-crate-metadata.json` (document URL) | Defects 1 and 2. A fragment id is also a fragment of the descriptor, not of the directory. |
| `urn:example:crate` | Defects 1 and 2. rdflib joins `x` onto the URN as `urn:example:crate/x`, where RFC 3986 gives `urn:x`. 27,230 of 60,000 ids differ from JSON-LD 1.1; no further merges. |

## Notes (below the bar)

- **Ill-formed IRIs pass.** The absolute and fragment branches check characters, not RFC 3987's grammar.
  - They accept `http://a/b#c#d`, `ab:%zz`, `ab:[x` and `#a%zz`. rdflib keeps all of them as written (MEASURED: `out_ill.json`).
  - A conforming conversion drops a node whose IRI is not well-formed (READ: API 8.1). The harm is BELIEVED.
  - The lead's class test accepts a tail ending `%-` and holding `[]`, while the prose says "an absolute IRI".
- **JSON-LD 1.0.** A 1.0 processor treats every context term as a prefix (BELIEVED; I had none to run). `geo`, `data`, `isbn`, `issn`, `url` and `email` are terms (MEASURED: context listing). The tests accept `geo:x` and cite 1.1, and the stated limits are silent on 1.0.
- **Path plus fragment.** `x#a` and `data/#a` are refused, though RDF reads them without a collision. The reason is given in a test, not in the prose.
  - I could not search P2's or P4's crate builders. The entry's "P1.1's code and tests write none of the refused forms (READ)" covers P1.1 only.
- **Test reach.**
  - The 30 tests named "refused by the id rule" cannot tell the id rule from the path rule. With Files exempted from the id rule (mutant 26), only `test_a_file_whose_id_begins_with_at_is_refused` fails, and only on the location, because `hasPart`'s reference still refuses the crate.
  - My mutant that also refuses `...` segments survives. That over-refusal is harmless.
  - The sweep's statement equals the code exactly (0 disagreements over 3,478,605 strings, MEASURED: `exhaust.py`). It adds a tail alphabet that item 22's prose does not state.
- **Layout and patterns.**
  - Item 22's closing paragraph has no blank line before it, so it probably renders as the tail of the fourth bullet (BELIEVED, CommonMark lazy continuation).
  - The three id patterns are private and use lookaheads, which XPath and SPARQL regex lack (BELIEVED). `PATTERNS` is "for P4's shapes to read".
  - `SPELLINGS["ref"]` and `docs/VOCABULARY.md:41` do not mention the id rule.
- **Timing.** CLAUDE.md says about 125 s for the full runner; I measured 167 s of stage time.

## What held

- **Rule against rdflib at P4's base.**
  - rdflib 7.6.0 resolves every accepted id as RFC 3986 says, with no merge, no blank node, no exception and no keyword, except Defect 1's fragments.
  - Evidence: 460,000 accepted ids over nine bases. A 400-id real `Graph.parse` sample agreed in both subject and object position.
- **Pyshacl and serialisers.** Pyshacl, N-Triples and Turtle round-tripped 4,000 accepted ids.
- **The lead's claims about the refused forms.** I reproduced them (40 ids, `file:///crate/`). For example `@x`, `@inner/not-first`, `//` and `.` are the root, `_:b0` is a blank node, and `../a` is `file:///a`.
- **Real-world absolute IRIs.** DOI, ORCID, SWH, urn, purl, mailto, tel, geo and `data:` ids are accepted and read as written.
- **Prefixes (item 2).**
  - `CONTEXT_PREFIXES` is exactly the 22 prefix terms of the pinned context plus `qro`, by JSON-LD 1.1's rule and by rdflib's code.
  - Empirically, rdflib expands `term:zzz` for exactly those 23 (my `3DModel` hit was a false positive from my own heuristic: it resolves as a relative path).
  - No other prefix rdflib knows (29 bound, 74 tried) is expanded.
  - Commands: `ctx_analyze.py`, `bound_prefixes.py`.
- **Old against new reader.**
  - 6,126 ids used three ways (entity id, reference, File id) gave 0 widened verdicts and 0 crashes.
  - 60,000 random edits to a fixture crate raised no non-Refused exception.
  - `id_problem` took 200,000 hostile strings with none raised, and ids of 1 MB in at most 40 ms.
- **Command line as a process.** The command line gives REFUSED lines and exit 1 on a crate with a refused id (the check ran on 9 fixture crates).
- **Mutation.** The lead's 14 mutants were killed, and 27 of my 28 were killed (the survivor is the harmless `...` over-refusal).
- **Item 11's limit.** It is true: `readme:hidden` is accepted, `README:hidden` is refused.

## What I did not do

- I did not read or run P4's shapes or any worktree. The SHACL consequence is shown only with my own small shapes.
- I ran no JSON-LD processor but rdflib 7.6.0. Nothing else was installed, and installing was barred. Claims about strict processors are READ from the specification (through WebFetch's extraction, a small model's quotes) or BELIEVED.
- I ran Python 3.12.9 only. I did not run urllib's `;` handling at 3.13 or 3.14.
- My draws are edge-biased samples, not a proof. I did not compare the live RO-Crate context with the pinned copy.
- I did not run the quick budget, or P0.4's full runner (only its test counts).
- I wrote one stray file outside `check\`, `/tmp/_sums_p05.txt` (a checksum list), and deleted it at once.
- I ran read-only `git status`, `git diff`, `git log`, `git ls-files` and `git archive` in the real repository.
- I printed no key, CRN or IBM job id. I connected to nothing but public specification pages. Nothing in the engine environment changed (0 files newer than my start).

**Paths.**
- Probes and demo crates: `<scratch>\verifier-P05-r1\check\probe\`
- Mutants and logs: `…\check\mut\`
- Runner log: `…\check\runner-full.log`
- Candidate-fix tree: `…\check\fixcompat\`
