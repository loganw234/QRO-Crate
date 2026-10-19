**Verdict: READY**, on the relaxed bar.

I found no defect in what the shipped code does, and no gate or registry that lets an accidental fault through. The notes below are all non-blocking. The code is unchanged since round 3 except one comment word in `qro/spelling.py` ("http, https, ftp or like base"). A `diff -rq` of the r3 and r4 trees shows seven files differ: FORMAT.md, VALIDATION.md, the reviews README, the new round3.md, that comment, a test_hostile.py docstring, and test_spelling.py's added cases.

## Freeze and runner
- **Freeze:** the brief begins `b2d2ec5e5bc46e4d` and SHA256SUMS.txt begins `4f0167950cd17fc6`. `sha256sum -c` gives 264 OK over the same file set. The 264 files are byte-equal to the live repo's working tree (MEASURED).
- **Full runner:** `QRO_MOTH_ROOT=<repos>/moth-quantum bash verify/run.sh` in a `git init` copy gave 17 passed, 0 failed, 7 skipped by name, exit 0. The stage times sum to 339 s on a loaded machine (MEASURED).
- **Quick budget:** 14 passed, 0 failed, 4 skipped (p1, p2, p4, profile).
- **Privacy stage:** passes with the lead's draft commit message committed in my copy.
- **Test counts:** docs 164, tool-tests 129, vocab-tests 12, format 958, custody 23, control-tests 32 (1,318), as the ledger says (`pytest --collect-only`).
- **Twin:** its body digest is `21fafec53bdc2c5d` at 20d40e6 and in the frozen tree, and it is ACCEPTED in both.
- **Old tests on new code:** 20d40e6's own tests against the new code give 5 failed and 714 passed. The five are the intended ones: the two `qro:RawResult` id cases, the `a%20b` raw-result case, the old `ref` class example, and the old sweep statement for `id`.

## Defects
None on the relaxed bar. I weighed notes 1 and 2 below hardest and did not block on either. Note 1 predates P0.5 and is contrived. Note 2 is a stated limit that only a 1.0-only processor reaches.

## Notes
1. **Older than P0.5, a hang and quadratic memory (code, identical at 20d40e6).**
   - The loop in `qro/reader.py` `_graph` builds every directory prefix of each local File's path, and the id rule accepts ids with no total length or segment cap.
   - A File id of 50,000 one-letter segments (100 KB) passes `reader.read` but took 149 s in the frozen tree and 205 s at 20d40e6. 20,000 segments took 9.0 s and 6.4 s. 5,000 took 0.17 s and 0.14 s.
   - Peak memory at 20d40e6 was 8 MB at 2,000 segments, 33 MB at 4,000 and 129 MB at 8,000, so it is quadratic. About 5 GB at 50,000 segments is my extrapolation (BELIEVED).
   - Scripts: `deep4.py`, `mem4.py`. A cap on @id length in `id_problem`, or incremental prefixes, would end it.
2. **The fourth stated limit is more exposed than it reads (stated limit).**
   - RO-Crate 1.3's structure page says the metadata document must be valid JSON-LD 1.0, in flattened and compacted form (READ, curl). The limit says only that the context names no version.
   - JSON-LD 1.0's own IRI expansion makes every term of the context a prefix (READ). 333 of the pinned context's 3,069 terms are scheme-shaped (MEASURED). `data`, `geo` and `isbn` are among them.
   - A 1.0-only reader would take `geo:1,2` and `http://schema.org/geo1,2` as one node. By my own model of the 1.0 rule (no real processor run), the pairs `geo:1,2`, `name:x`, `data:x` and `url:x` against their `http://schema.org/…` expansions merge. The checker accepts those pairs through step 8, and step 9 refuses them only because the fixture generator does not make them (`one0_4.py`).
   - JSON-LD 1.1 sets the prefix flag only for a simple term ending in a gen-delim, with no processing-mode condition (READ). rdflib with `version=1.0` reads 90,000 accepted ids at 5 bases exactly as in 1.1 mode (`v10_4.py`). So only an implementation of the 2014 recommendation is exposed.
   - Closing it would mean refusing absolute IRIs whose scheme is one of those 333 names, `data:` and `geo:` among them. I judged it not a code defect on this bar, but the owner may want to decide it.
3. **Limit 3's prose (prose).** "Leaves a relative id relative and makes no node of it" is false for a fragment holding `:`. At `mailto:`, `s3:` and `data:` bases, `#a:b` makes the relative IRI `.#a:b`, and other fragments make no node (`mailto4.py`). rdflib has other base departures item 22 does not list:
   - a `//` in the base path collapses;
   - dot segments in the base path are normalised;
   - a final `;` in the base is dropped for fragment ids;
   - the scheme is lowercased.

   None merges two accepted ids.
4. **Item 22's measured list (prose).** "Are the root" for `@x`, `//`, `?` and `;` holds at a directory base such as P4's `file:///crate/`. Where the crate is read from its metadata file's URL, those four read as the descriptor's IRI (`claims4.py`).
5. **Test reach where the code is right.**
   - A mutant that exempts a compact IRI whose suffix begins `//` (`schema://x`) survives every stage. No reader misreads that id: rdflib keeps it as written, and JSON-LD 1.1 returns it as is (READ). The prefix test's docstring "Whatever its tail" over-claims.
   - `CONTEXT_PREFIXES` is not derived from `V.context()[1]`, and its test unions only `V.PREFIX`. A second profile prefix added later would go unseen.
6. **Other.**
   - The draft commit message still holds the token `VERDICT_LINE`.
   - CLAUDE.md's stage timings are P0.6's, as before.

## What held
- **Context.resolve, rdflib 7.6.0 under 3.12.9 (`run4.py`).**
  - I used 412,557 accepted ids: exhaustive token products, neighbours of seeds, and random draws up to 60 characters. They were read at 43 bases: file in four forms, http/https in many forms, 17 other joinable schemes, 8 non-joinable ones, 3 urn forms.
  - Result: 0 blank nodes, 0 exceptions, and 0 merges of two relative ids or of two absolute ids at any base.
  - It differs from RFC 3986 only at six bases whose own path is odd (empty, `/..`, a final `/.`, `//`, a final `;`). No merge arises there.
- **Real parses.** 27,991 ids at 14 bases, in subject and object position, equal the Context.resolve readings, and 3.13.5's digests equal 3.12.9's.
- **The `;` rule (`semi4.py`).** 526,107 accepted ids containing `;` were read through urljoin at 15 bases, giving 7,891,605 readings per Python. None differs from RFC 3986 under 3.12.9 or 3.13.5. The eleven schemes are confirmed (`schemes4.py`).
- **urllib.** `urlsplit`, `urlparse`, `urldefrag` and `urljoin` at six bases raise on none of 1,031,410 accepted ids, under both Pythons (`raise4.py`).
- **The gate's model (`mvr4.py`).** The test's `rdflib_reads` equals Context.resolve on 3,870,043 readings per Python (90,001 ids at 43 bases). The test's `rfc3986` equals my resolver on every relative id at every non-urn base. My resolver passes all 42 of RFC 3986 section 5.4's examples as read from the RFC text.
- **Property test and reach.** The property test, its control test, the trailing-hash test and the RFC examples pass directly under 3.13.5 (`prop313.py`). The draw gives 11,667 accepted ids, with 335 `://` and 672 `;` refusals against thresholds of 300.
- **Prefixes (`prefix_audit.py`).** rdflib holds exactly 23 prefix terms, equal to `CONTEXT_PREFIXES`, in both context forms. The pinned context has no `@vocab`, keyword alias or expanded definition.
- **Term names as ids.** 9,297 ids built from every term name and keyword name read as plain relative ids, with no duplicates (`terms4.py`).
- **Long ids.** 42,552 structured ids up to 80,000 characters read as base-head plus id (`long4.py`).
- **Other readers of the output.** rdflib's nt, turtle, n3, xml and json-ld serialisers round-trip 6,000 to 8,000 accepted ids at three bases. pyshacl 0.40.1 conforms on 6,000 accepted ids at two bases, one IRI node each (`serial4.py`, `shacl4.py`).
- **Old against new reader (`diff4.py`, `cmp4.py`).**
  - I planted 90,903 ids four ways each, 363,612 verdicts per tree. Nothing was newly accepted, nothing crashed, and no id the rule accepts changed verdict. Every new refusal is `spelling`.
  - The command line on 153 crates exits 0 or 1 only, with no traceback. Five Files changed, as intended: `x;`, `;`, `.;x`, `..;x` and `@x` (`cli4.py`).
- **References.** Item 22's two names hold for every refused reference: `graph-form` for 65,968 non-absolute ones and `spelling` for 6,047 absolute ones (`refnames4.py`).
- **Rule against prose.** `id_problem` equals my own reading of item 22 on 863,419 strings (`prose4.py`).
- **No ReDoS.** The worst case, a 2 MB id, took 0.51 s (`redos4.py`).
- **Mutants.** The lead's 42 are all killed again. Of my 19 (`m_r4.py`), 16 were killed by targeted tests. The three survivors are the `//` exemption in note 5 and two equivalent mutants (a `{2,}` hex run, and a `':' not in value` guard on a pattern with no colon).
- **Round 3's fixes.**
  - D1 is true: item 22 now says JSON-LD 1.1, and rdflib keeps `http://example.org/a/../b` and `http://example.org/b` as two nodes.
  - D2's two test comments are true.
  - The `@0` and any-tail compact IRI tests exist and kill the three survivors.
  - The model docstring is true.
  - The 3.13.5 figure holds with rdflib itself.
  - The eleven schemes are right.
  - "One spelling is as RDF compares IRIs" holds: 12 case and escape variants make 12 nodes.
- **Placed reviews.** The redaction counts (2, 1, 1), the escapes and the LF-only endings match the README. No line ending differs from 20d40e6 in any changed file.

## What I did not do
- **Processors:** I ran no JSON-LD processor but rdflib 7.6.0. I ran no 2014-recommendation 1.0 processor, no Python 3.14, and no other patch release of 3.12 or 3.13. Spec text was read by `curl` of the public pages.
- **Parcels:** I did not read the parcels' trees or worktrees, so "P1.1's 1,018 tests pass" and "P4's 100 ids pass" are unchecked by me.
- **P4:** P4's shapes and the p4-shacl stage are not in this tree.
- **Reviews and timing:** I did not check the reviews' source SHA-256s against their transcripts, or the lead's 199 s timing.
- **Id sets:** mine are bounded by alphabet and length, plus random draws.

Housekeeping, all mine:
- **Frozen packet:** my `prefix_audit.py` imported `qro` from `frozen\tree` with `python -I` and wrote two `.pyc` files into `frozen\tree\qro\__pycache__`. I noticed it later, deleted exactly those files and the directory, and re-verified. `frozen\tree` again holds 264 files, with 264 OK, no `__pycache__`, and the same SHA256SUMS hash.
- **Stray list files:** I wrote two small list files to the system temp early on and deleted them.
- **pytest temp dirs:** the runner and mutant runs used the system temp, as the project's tests do.
- **Directory listing:** once I listed directory names, depth 4, under `AppData\Local\qro-crate`, which showed the lead's scratch and the parcels' agent folder names. I read no file there.
- **Engine and 3.13 packages:** no file in the engine venv or in 3.13's rdflib directory was created or changed after my start.

All paths below are under `<scratch>\verifier-P05-r4\check\`:
- `mine\` — scripts
- `mut\` — mutants and logs
- `runner_full.log`, `runner_quick.log`
- `spec\` — downloaded spec pages
- `work\tree` — the runner copy
