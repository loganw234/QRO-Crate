**Verdict: READY**, on the relaxed bar (CLAUDE.md item 6: only a defect in what the code does blocks).

I found no blocking defect of the four kinds the brief lists:
- no wrong acceptance or refusal, crash, hang or wrong exit in the generator, evaluator, engine stage, shapes or examples that a crate or tree state can reach;
- no must shape that claims more than the checker holds;
- nothing read, written or removed through a link or outside `profile/` that changes a byte or a verdict;
- no gate or test that passes a fault it claims to catch while the shipped code is wrong.

I found six things about what the code does, all low in reach, none changing a verdict or a byte (section 2). One of them, C1, is the single place where "a link is never read through" is literally untrue: a metadata `stat`, new this round. I do not count it toward the verdict, as the fourth verifier did not count its low-reach items, but the lead may rule otherwise.

Labels: MEASURED (a command, run through `sbx.sh` from `<home>AppData\LocalLow\qro-sbx\p4-r5` unless I say `sbx-mid.sh`), READ, BELIEVED. Scripts are in `p4-r5\scripts\`, logs in `p4-r5\logs\`, and my running notes in `SCRATCH\verifier-P4-r5\check\notes.md`. The Write tool refused a `report.md` there, so this message is the report.

## 1. Freeze and runs

- **Freeze (MEASURED, `sha256sum`).**
  - SHA256SUMS.txt begins `054c518e2ff900fb`; ledger-P4, ledger-lead, brief-build and brief-fix begin as the brief names them.
  - `sha256sum -c` over frozen\tree: 350 of 350 OK. The same over the worktree `QRO-Crate-P4`, read only: all OK. Both re-checked at the end: unchanged.
  - `git archive 37640f0` (291 files) against the tree differs only by P4's added files and `docs/README.md`.
  - Against P4's round-4 freeze (the builder's `f0`, read only), `qro/p4_shapes.py`, `p4_eval.py`, `p4_expand.py`, `p4_model.py`, `p4_examples.py` and `p4_turtle.py` are byte-identical.
  - This round changed `tools/gen_profile.py`, `qro/p4_profile.py`, the engine runner, the generated files, `docs/P4.md` and the tests.
- **Runner (MEASURED).** My copy, `git init`, commit 2f9d94a, `bash sbx-mid.sh bash verify/run.sh` with `QRO_MOTH_ROOT` and `QRO_SHACL_PYTHON` set.
  - Run `20261026-144130-44730-2f9d94a`: 21 passed, 0 failed, 3 skipped by name (p2, p1-crates, p2-crates), exit 0. p4 92 s, p4-shacl 236 s, about 650 s of stage time beside my own sweeps.
  - `pytest --collect-only` gives p4 920 and p4-shacl 236, as the ledger says.
  - All of `tests/p4` again at low integrity through `sbx.sh`: 920 passed in 140 s. `git status` of the copy afterwards: clean.

## 2. About what the code does (low reach, not counted toward the verdict)

- **C1. `--check` asks the OS about paths behind a link that stands where a rendered directory goes. New this round.**
  - Cause (READ): `drift()` now calls `(root / "profile" / rel).is_dir()` for a rendered path that is not on disk. Round 4's `drift()` did not.
  - Fault (MEASURED, `python -B scripts/stat_through.py`): with a junction at `profile/validator`, `--check` makes five `os.stat` calls on `profile/validator/qro-crate/...` while the link is there. `--write` makes none while a link exists.
  - Effect: existence and type only. Both answers append a problem, so the exit code never changes. The text changes only if the target holds a directory at that path: the line then reads "is a directory ... run --write removes it", though `--write` would remove the link, not the directory.
  - It contradicts "never read through" in the docstring and in docs/P4.md.
  - A small fix: take the directory case from `have` and `empty_dirs`, or ask only when no ancestor under `profile/` is a link. Add a test that spies `stat` under a link below `profile/`.
- **C2.** An unreadable `context.jsonld` (held open with no sharing, MEASURED) is exit 1 "cannot be read (PermissionError)". An unreadable rendered file, stray or fixture file is exit 3 (MEASURED). A test pins the exit 1 and the sentence. The docstring's list of what is exit 1 does not name P0's context.
- **C3.** `--write` now removes strays, then empty directories, then writes.
  - A directory that cannot be removed fails the run with exit 3 before any file is written. I measured an empty stray that is a shell's working directory: WinError 32, "it had finished writing no file".
  - Round 4's order would have written first. This follows from the ruling and is not stated.
- **C4.** In a case-clash directory, `--check` says of a stray inside it "rendered by no definition; run --write" while `--write` refuses (MEASURED, `Examples/zzz.txt`). The clash line is in the same output.
- **C5.** The evaluator raises ValueError (`int()` over the digit limit) on an `xsd:integer` literal of more than 4,300 digits, where pyshacl calls it ill-typed (MEASURED, `int_forms.py`). No crate reaches it, because `json.loads` refuses such a number first and the reader says `spelling`. Limit 23 does not mention it.
- **C6.** The "removed ..." and "profile/... rendered by no definition" lines print a stray's name raw, not through `escape`. Non-ASCII names reach the output as they are (MEASURED). Windows forbids control characters in names, so I could not try a newline.

## 3. What held

- **D1 (MEASURED, `atk_jct.py`, `atk_inproc.py`).** `profile/` itself as a junction, in both modes, to:
  - a full copy plus a victim file and an empty directory;
  - an exact copy;
  - nothing (dangling);
  - the tree's own root, with files that sort before the link;
  - a directory inside the tree;
  - a chain j1 to j2 to outside;
  - a target that holds a junction back to the root;
  - `tools/`.
  Every case: exit 1, the one LINKED sentence on stderr, stdout empty, targets equal byte for byte, the link still there, the tree unchanged. With an audit hook on open, scandir, listdir, walk, remove, rename and mkdir, there were zero events under the link or under its target.
- **Other links (MEASURED).** Junctions under `profile/`:
  - at eight stray places;
  - at the paths of five top-level, four deep and three deeper rendered names;
  - at `context.jsonld`;
  - dangling;
  - to the root, to their own parent, and to `profile/` itself.
  The link goes, no target changes, and the second `--check` is 0. `context.jsonld` as a junction is exit 1 "is a link" in both modes. The audit hook (`atk_inproc2.py`) shows no event behind any link. C1 is the exception, since a `stat` is invisible to it; I wrapped `os.stat` in `stat_through.py`.
- **Hard links.** Five states: at `README.md` to an outside file, two rendered names that are one file, a stray to an outside file, a stray to a rendered file, `context.jsonld`, the metadata. `--write` replaces the place, the other name keeps its bytes, nlink is 1 afterwards, and the second `--check` is 0.
- **Case.** Six renames at several depths: both modes exit 1, one line each, tree unchanged. `EXAMPLEſ.md` and `context.jſonld` (U+017F) coexist with `EXAMPLES.md` and `context.jsonld` on NTFS, and the tool still refuses them as a clash. That is the stated `casefold` limit.
- **A directory where a file goes.** Eleven states (empty, with a stray, nested empties, at the metadata, at `notes.txt`, at a `.ttl` with a file in it, a file where `validator/` or `examples/fixture/` goes, `README.md.tmp` as a directory and as a file). `--write` 0, then `--check` 0, then `--write` 0. A directory at `context.jsonld`: exit 1 in both modes, kept.
- **Unlistable directory (simulated).** I could not make a real one, because the guard refuses the extended paths. With `os.scandir` made to raise, in process and as a process, for `profile/` itself, a nested stray and the fixture's `data/`:
  - Error types tried: PermissionError, OSError, FileNotFoundError, NotADirectoryError.
  - Result: exit 3 in both modes with the directory named, and nothing removed.
  - On the second listing only, the strays were already gone and the run fails with exit 3.
- **Exits and crashes (MEASURED).**
  - `-OO` and the other flags: `--check` is 0 under `-O -OO -I -E -s -P -q -u -b -bb -X dev -X utf8 -W error`, and `-OO --write` writes the committed bytes. No arguments, both, or an unknown flag: 2. `--help`: 0.
  - Eight import failures (missing module, syntax error, `SystemExit(0)`, `KeyboardInterrupt`, an exception whose `__str__` raises, no `qro`, a module raising `MemoryError` at import, `SystemExit(2)`): exit 3, one line, `profile/` untouched.
  - A failure at the third `os.replace`: exit 3, names what finished, no `.tmp` left, the next run converges.
  - A rendered, stray or fixture file held open: exit 3.
  - `sys.stdout`, `sys.stderr` or both `None`: the exit is the verdict.
  - A reader that has gone: `--write` prints its FAILED line and Python ends it with 120, as the docstring says.
- **Read-only.** A read-only stray, rendered file, or file in a directory where a rendered file goes: `--write` exit 3, names what it finished, no `.tmp` (stated limit). Hidden, system, archive, offline, temporary and not-indexed attributes have no effect.
- **Determinism and paths.** `--write` into fresh copies under twelve environments, plus `-OO`, `-X utf8` and `-X dev`, gives the committed bytes each time. A root with spaces, CJK or accents, and a TEMP that is long, spaced or CJK: `--check` 0 and `--write` 0. A 4 MB drifted file and a million-line one: `--check` takes 1.5 to 2.6 s. Thirty-seven awkward stray names are handled in both modes and stay ASCII-safe under `ascii` and `cp1252`.
- **State fuzz (`fuzz_states.py`, in process).**
  - 600 random trees (seeds 21 and 22), each one to four of 21 kinds of state: strays, junctions to outside directories, to the root and to `profile/`, dangling junctions, hard links, case variants, directories where files go, files where directories go, drift, deletions, `.tmp` leftovers.
  - Invariants: `--check` changes nothing; nothing outside `profile/` changes; `--write` exit 0 leaves exactly the committed `profile/` and `--check` 0; `--write` exit 1 leaves the tree unchanged; no exit 3.
  - Result: **0 violations** (492 trees `--write` 0, 108 refused with exit 1).
- **The Profile Crate.** An independent audit (`audit_profile.py`) of 12 files: the metadata itself and 11 others, each of the 11 listed with its true sha256 and size. None unlisted, no `File` entity without a file, ASCII, no CR.
- **Numbers in the documents** (counted, `doc_numbers.py`): 12,591 pool edits, 469 family crates, 124 alias crates, 18 `ref` terms, 57 `qro:` terms and types, 23 limits, 3 integer terms, 139 shapes (131 must, 8 should). All as stated.
- **Limit 2 and the banner.** With the runner's four guard lines verbatim and `-I` (`inf_engine.py`): inference none gives 0 results, rdfs 94, owlrl 112, both 527, as quoted.
- **Limit 23.** I enumerated 765 forms of an `xsd:integer` literal on the committed `term-qro-shots` shape in one engine job (`int_forms.py`).
  - The two judges agree on 38 forms.
  - The evaluator fails and pyshacl accepts 726: 670 non-ASCII decimal digits, 50 forms with one of 25 white-space characters before or after the `1`, mixed scripts, underscores, and a no-break-space or tab on both sides.
  - The reverse (evaluator accepts, pyshacl fails): none.
  - So the eleven forms are examples of three kinds, and the kinds are complete in this enumeration. What limit 23 says of them is true.
  - U+001C to U+001F around the `1`: `int()` does not read them (ASCII control characters) and both judges fail them.
  - READ (WebFetch of the SHACL Recommendation): 4.4.1 keeps `sh:minLength` violated by a blank node even when the parameter is 0, so the evaluator is right and pyshacl 0.40.1 is not. 4.3.4 violates when `$maxInclusive &gt;= v` does not return true, so a boolean violates. 4.1.2 defers "ill-typed" to RDF 1.1 Concepts and says nothing of white space, so who is right on white space stays unsettled, as limit 23 says.

## 4. Soundness, the design's central claim

- **P4's pool on richer bases (MEASURED, `rich_sweep.py`).** The first verifier's 12,591-edit pool, which P4 runs on the six-entity fixture, run on seven valid bases of my own. Each base is accepted by steps 1 to 3 with no must shape failing. The bases are:
  - one entity of every table type with all its terms (20 entities);
  - nested Datasets with Files on disk;
  - a CreateAction with instrument, object and result, plus a `qro:Job`;
  - a remote File, a fragment File and a CreativeWork;
  - one entity typed CreateAction, `qro:Job`, `qro:Pub` and `qro:Decode` with all their terms;
  - a second raw result;
  - all of these together (33 entities).
  **203,837 single-edit crates judged: A (a must shape fails while steps 1 to 3 accept) 0, B (a must shape fails and no failing shape claims the checker's refusal) 0, U (accepted but the expansion cannot read it) 0.**
- **A real engine, no inference (`engine_diff.py`, `engine_combo.py`, P4's own runner and helpers).** 5,315 crates through pyshacl 0.40.1:
  - 925 on the fixture; 1,200 on each of two rich bases and 1,090 on a third (up to 400 checker-accepted crates, 500 that fail, 300 that conform though refused, fewer on the smallest base);
  - 900 with two or three pool edits at once.
  Engine errors 0; failing must-shape sets differ 0; (shape, focus) pairs differ 0; triples rdflib makes differ from the expansion's 0; A 0; B 0.
- **Random shapes over random graphs (`rand_diff.py`, the runner's `graph` job).** 11,000 cases (seeds 3 to 5) of the constructs the generated shapes use: targets of four kinds, node and property shapes, `sh:or`, `sh:not`, `sh:closed` with ignored properties, qualified value shapes over inverse and one-or-more paths, `sh:in`, `sh:hasValue`, patterns, lengths, bounds, counts. 0 disagreements, 0 errors.
  - Two naming artifacts, neither a verdict: for a result of a property shape nested in another, pyshacl names the outer value node as focus where the evaluator names the top focus (I compare focus sets only where no property shape nests another); and rdflib writes `"1"^^xsd:boolean` as `true`.
  - `sh:not []`, `sh:or ([] [IRI])`, `sh:in ()` and a qualified `[]`, which no generated shape uses, also agree.
- **Spellings and structure.** 62 odd JSON values (floats, `None`, booleans, nested lists and objects, integers past 2^63, odd strings) against every spelling and word set through `qro/spelling.py`, the expansion and the shapes, plus 480 whole-crate reads through `reader.read`: 0 accepted-yet-failing. Sixty-eight hand-made structural crates (34 variants on two bases) agree across checker, evaluator and engine. They include a root that lists itself or the descriptor, a Dataset that lists the root or itself, two parents, a cycle, an unreachable cycle, a Dataset with no slash, an absolute Dataset in the chain, and ids with percent signs, tildes or 300 characters.

## 5. Mutation (MEASURED)

- **P4's own mutants, re-run by me.** I copied their `hm_p4.py` and `defs_resume5.py` into `p4-r5\scripts\p4theirs\`, read them first, and ran them through `sbx.sh` on my copy with their baselines first. Groups L, G, R, W (46) and C, D, U, X, P, E, O (56): **102 of 102 killed**, each by a named test, workers pristine afterwards. I did not re-run the 39 that need the engine (T, N, Z) or are ports of earlier rounds.
- **My own 24 of `tools/gen_profile.py` and `qro/p4_profile.py`** (`mut_gen.py`, through `hm_p4r5.py` = `hm_t.py` with its fallback stage cut and the same refusal of a WORK outside the sandbox). Baseline of the three test files first: 117 passed. 17 killed, 1 not applicable (my text), **6 survived**:
  - V01 (links taken from directories only) and V02 (a link left among the files): equivalent on this host, since a junction always lists as a directory and a file symlink cannot be made here.
  - V06: `casefold` replaced by `lower`.
  - V16: `NotADirectoryError` no longer called "missing" (message only).
  - V20: `flush` dropped on the removal line.
  - V21: removals left out of the "finished writing" list in a failure line.
  Each is a test gap with the shipped code right.
- **My own 16 of the shapes and the evaluator** (`mut_shapes.py`): a length or bound one short, a text of two characters, the last term not allowed on an entity, a term single-valued, `file-reached` direct parts only, a qualified minimum one too high, closed shapes forgetting the ignored list, and similar. **16 of 16 killed.**

## 6. Notes

**Prose.**
- The docstring of `tools/gen_profile.py` and docs/P4.md "Links" say a link is "never read through", "without exception". C1 is the exception.
- The docstring and docs/P4.md "Stated limits of the tool" state the `casefold` limit in one direction only: a name the host calls the same and `casefold` does not is a stray, and removed. The other direction is not said. A name `casefold` equates and NTFS keeps distinct (the U+017F names, MEASURED) is refused as a clash until removed by hand.
- The exit-1 list in the docstring and on the page does not name P0's context (missing, a link, a directory, unreadable: all exit 1).
- Limit 2 says "with OWL-RL `owl:Thing`, `rdfs:Datatype`". OWL-RL alone adds `owl:Class`, `owl:AnnotationProperty`, `rdfs:Datatype` and others; `owl:Thing` and `rdfs:Resource` come with `both` (MEASURED, `inf_driver.py`).
- The banners of `2_terms.ttl`, `3_domains.ttl` and `1_absence.ttl` name three shapes that all live in `1_structure.ttl`.
- `--help` prints a cut sentence as the description ("... refuse drift (P4's design, items 1 and 8;"), and `--write` and `--check` have no help text.
- Ledger, not tree: it says the file-symlink branch of the walk is "held by a junction". No test holds it (V01, V02).

**Test gaps (shipped code right).** No test makes a symbolic link to a file (the host cannot; a Linux CI would need one). None pins `casefold` against `lower`. None puts a file at `profile` for `read_context` (V16). None checks that removals are named in a failure line (V21). None spies `stat` behind a link below `profile/` (C1). None runs the tool with its working directory inside a directory it must remove (C3).

## 7. What I did not do

- No real unlistable directory (simulated), no symbolic link (WinError 1314), no POSIX host, no Python other than 3.12.15, no rocrate-validator and no second engine. I fetched neither RDF 1.1 Concepts nor XSD.
- I did not re-run 39 of P4's 141 mutants (the engine-stage T, N, Z and the earlier-round ports). I did not run the engine stage at low integrity, since it ran at normal integrity in the runner as the brief says, nor the quick budget separately.
- I used the engine only as the runner does (`run_engine`, its interpreter, `-I`, its guard). Two scripts of mine copy the guard's four lines verbatim and vary only pyshacl's `inference` or the data.
- **Slips, mine.**
  - An empty `python - &lt;&lt;EOF` heredoc and a `python3 --version` (not found) in my own shell, outside the launcher: no script and no project code ran.
  - Two of my own scripts patched with `sed -i` and a `cat &gt;&gt;` heredoc instead of Edit.
  - One redirect to `/tmp_old_names.txt` (the MSYS root, not /tmp; no file was made, MEASURED), and one `ls /tmp | head -3 &gt; /dev/null` whose output I discarded. I wrote nothing to the owner's Temp folder.
  - A script of mine named `numbers.py` shadowed the standard module in one run; renamed.
  - I made 22 junctions inside my own directory and removed them with `scripts\cleanup_links.py` (the links only; 0 left, MEASURED).
- No IBM job id was printed or written. I touched nothing in frozen\, the worktrees, the ledger, other agents' directories, the launchers or the engine's environment.
