**Verdict: NOT READY.**

The design's central property held under every attack I made. Two defects stand. The first is in what `tools/gen_profile.py --write` does, with a test and docstrings that say the opposite. The second is two sentences in the stated limits that are false as written. Both are small to fix.

## The freeze and the runs

- **Freeze (MEASURED, `sha256sum -c`).**
  - All 347 files of tree\ are OK, and `SHA256SUMS.txt` begins `66e0e54992aa26b9`.
  - The five copies in the packet match their prefixes.
  - P4's worktree holds the same 347 bytes, hashed read-only.
  - I checked again after my work: still 347 OK, no stray directories.
  - Against 37640f0 the packet changes only `docs/README.md` (the two index lines). The other 56 files are new and are P4's.
- **Full runner (MEASURED, in a git copy of 37640f0 with P4's files over it).**
  - Run `20261026-060411-58615-ded2447+dirty`: 21 passed, 0 failed, 3 skipped by name (p2, p1-crates, p2-crates), 484 s.
  - Tests: p4 837, p4-shacl 229, p1 1,169.
  - No stray files were left.
- **Quick budget (MEASURED).** 17 passed, 1 skipped by name (p2), 188 s.
- **Engine variable (MEASURED).** Without `QRO_SHACL_PYTHON`, p4-shacl is skipped by name. With an interpreter lacking pyshacl, 9 tests fail loudly.
- **Test order (MEASURED).** tests/p4 passes reversed and shuffled, 837 each.

## Round 2's fixes hold

- **Defect 1, the three families.**
  - I re-ran the second verifier's probes f1, f2, f3 and f4. Every failing shape now claims the checker's name.
  - The families are what P4 says: 469 = 388 + 13 + 68, none in the 12,591-edit pool.
  - `families_probe_r3.py` gives 0 unclaimed with the six names. With the old two names it gives 49 crates in 20 classes, as P4 states.
  - All 131 must shapes in the committed Turtle claim all six names. The 8 should shapes claim none.
- **Pin of the four names left out of `FORM`.** My own reading finds each claimed wherever it can come first. This is reasoning, plus P1-crate sweeps in which a must shape failed under `field-kind` (1,044), `file-digest` (38), `raw-form` (18), `raw-digest` (6) and `file-unlisted` (1), with no unclaimed refusal.
- **Defect 2, the gate.** The sweeps now make the three families. The engine stage reads 213 crates: 128 + 4 + 13 + 68. It fails a must shape on 6 of the 8 context variants and on all 5 top-level keys.
- **`file-link` plant.** A junction at `data/jct` is refused as `REFUSED file-link at data/jct`, exit 1, through the real command line.
- **Defect 3, the eight sentences.** I found the old wording gone from all eight places. One stale test name remains (note 2).
- **Notes' tests.** I removed `-I` from `run_engine`: only the `-I` test fails. I moved the guard after the engine's imports: only the order test fails. Both are killed by the tests meant to catch them.
- **Limit 23.** The two disagreements reproduce. In 9,000 new random shape-and-graph cases, pyshacl differed from the evaluator in 7, all of them `sh:minLength 0` on a blank node. The Recommendation says a blank node violates a length bound (READ, section 4.4.1, through WebFetch's extraction). The limit's reason clause is wrong (defect 2).

## Defects

### 1. [code, with a gate and prose that claim the opposite] The generator follows a directory junction in `profile/`, and `--write` deletes the files it finds through it

- **Fault (MEASURED).** `python -B <scratch>\verifier-P4-r3\check\exp\scripts\junction_repro.py &lt;tree&gt;` copies the tree to a temp directory and makes a junction `profile/jct` to a directory outside it. The junction is made with `_winapi.CreateJunction`, which needs no privilege.
  - `--check` exits 1 with `profile/jct/victim.txt is rendered by no definition`.
  - `--write` exits 0 and prints `removed jct/victim.txt`.
  - The file outside the tree is gone, and so is the junction.
- **Cause.** On Windows, `os.walk(followlinks=False)` descends a junction, because `Path.is_symlink()` is false for one (`is_junction()` is true). `on_disk()` tests only `is_symlink()`.
- **False claims.**
  - `tools/gen_profile.py:55`: "links not followed; a link is reported by its path".
  - `tools/gen_profile.py:66-67`: "A link to a directory is not walked".
  - `tests/p4/test_p4_tool.py:67-70`: "never followed. Windows makes none here without a privilege".
  - P4 makes a junction itself in this round, and the project calls a junction a link (FORMAT.md item 12, `checker._is_link`).
- **Gate.** `test_no_walk_over_profile_follows_a_link` passes. It reads only the `followlinks=False` keyword.
- **Reach.** The precondition is rare, but the harm is deletion outside the tree. Fixing it means treating a junction like a symbolic link in `on_disk`, `empty_dirs` and the cleanup, adding a junction test, and restating the three sentences.

### 2. [prose] Two sentences in the stated limits are false as written

- **Limit 23:** "since a length bound is only 1".
  - MEASURED over `H.build()`: `min_length` is always 1 (13 shapes), but `max_length` takes the values 10, 19, 40, 64 and 2,002.
  - What is true, and what the test holds, is that no `sh:minLength` is below 1.
- **Limit 4:** "A remote File carrying a sha256 conforms." No test holds it.
  - MEASURED (`remote_probe.py`): an `https:` File with a sha256 fails `file-reached` unless the root also lists it. Listed, it conforms.
  - The failing shape claims `graph-form`, which is the checker's name for that crate.

## Notes (below the bar)

1. **Prose.** `tests/p4/p4_sweeps.py` line 25 ends "the families @COST@." The template token was never filled.
2. **Prose.** `tests/p4/test_p4_gates.py:122` is named `..._claims_the_two_of_form`. `FORM` is six names.
3. **Prose.** `p4_sweeps.py:18` says the walk "refuses a link before everything". The reader runs before the walk.
4. **Code, exotic.** `--write` prints a removed file's name unescaped. A stray file whose name the console code page lacks makes it exit 3 after removing the file and before writing anything (MEASURED, `é中.txt` on cp1252).
5. **Test reach.** The pin stops at step 2. Step 3's `count-unpaid` is claimed by no shape. That is true today, because no one-edit crate makes a must shape fail under it, but nothing pins it.
6. **Design consequence.** Each must shape now claims 6 of the 10 refusals of steps 1 and 2. The `qs:claims` of a shape therefore says little, and the README says so.
7. **Lead's, already known.** The quick budget is 188 s here against CLAUDE.md's "about 70 s".

## What I tried that found nothing

All of these are MEASURED; the scripts are in the `exp\scripts\` directory beside `junction_repro.py`.

- **Soundness, A (a must shape fails on an accepted crate).**
  - 6,400 random valid crates from my own generator `gen_valid.py` (not P4's): 6,398 accepted, A = 0. The 2 refused were my generator's own case clashes. The engine agreed with the evaluator on 460.
  - 145,884 term-and-value crates through the real reader (`spell_diff.py`, every code point to U+31FF for text): 138,884 accepted, A = 0. The engine agreed on 600.
- **Soundness, B (a refusal no failing shape claims).**
  - Single edits of P1's synthetic crates (`e2_p1edits.py`): IBM-shaped seed 7, 21,598 edits; Atlas-shaped seed 8, 7,743. A = 0 and B = 0 in both.
- **Evaluator against engine.**
  - 4,000 edited crates (`e4_diff.py`): 0 differences in triples or in failing (shape, focus, severity).
  - 72,891 fresh accepted ids (`id_fuzz.py`, new seed and alphabet): 0 differ from rdflib.
- **Limit 3.** Every way a shape is looser than the checker, among the spellings the table uses, is in limit 3's list. `binary64` and `iri` have no term yet.
- **Generator exits.** 0, 1, 2 and 3 all come out as documented, and a closed pipe gives 120. Eight renders (four hash seeds by two time zones, from another directory) were identical.
- **Requirements file.** Byte-identical to the lead's copy, hashed with `cmp` and `sha256sum` (that one file, nothing else read there).
- **Profile Crate.** Read against RO-Crate 1.3's profiles page (READ, WebFetch): every MUST it names is met. The SHOULDs not met are stated limits 9, 11, 17 and 22.
- **Example crate.** Accepted with `--fixtures`, and `step-unbuilt` without.
- **Mutants.** Four of mine, all killed: `-I` removed, guard moved, engine ignoring a crate's own context, and the early verdict skipping step 3.

## What I did not do

- I did not run rocrate-validator, a second SHACL engine, or P0.6's gate.
- I did not re-run P4's 48 mutants. I made 4 of my own.
- I did not test symbolic links; the host cannot make one.
- My sweeps are samples.
- I read the new test files and the pins in full, not every test body.
- I used the engine only through P4's runner (`-I`, guard first). Beyond the repository's shapes and crates, I also fed it random small shapes and graphs through the runner's `graph` job, as P4's micro cases and the second verifier did.
- **Slips.**
  - Once, in my first listing, an IBM job-id file name from `records/` appeared unmasked in my console. I wrote it nowhere, and it is masked here.
  - I wrote four small list files to the system temp. They are deleted, as are the temp crate directories my scripts left.
- I touched nothing in frozen\, the worktrees, the ledger, P4's scratch (I ran a modified copy of one of its scripts from my own directory), the earlier verifiers' directories, or the engine's environment.
