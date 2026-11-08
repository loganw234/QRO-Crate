# P4.2, first verifier, on the full bar

## Verdict: NOT READY

I found two defects, one in a gate and one in prose. I found no defect in the tool, the evaluator, the engine stage, the shapes or the examples. The code does what the rulings ask. The gate defect is in the spy that holds C1, and it is a regression against main. Both are small to mend.

Every claim below is MEASURED unless marked READ or BELIEVED. The commands are in `check\notes.md` under SCRATCH\verifier-P42-r1\check\. My scripts and logs are in `<home>AppData\LocalLow\qro-sbx\p42-r1\`. The main commands were:
- `sha256sum -c` over the tree and over the builder's worktree.
- The full runner through `sbx-mid.sh` on the packet committed as 08d6764.
- `gen_profile.py --write` in a fresh copy, then `diff -r`.
- `scripts/hm_r1.py` (the seventh verifier's harness, re-aimed) with `defs_r1a.py` to `defs_r1d.py`.
- `scripts/spy_all.py`, `diff_tools.py`, `probe_host.py` and `probe_digits.py`.
- `inf_probe.py` under the engine's interpreter with `-I`.

## Defects

**D1. Gate: the spy that replaced `watch_reads` does not read keyword arguments, so mutants that main's test kills survive P4.2's.**

- **The fault that shows it.** In `tools/gen_profile.py`, in `_run`, put a swallowed `os.listdir(path=root / "profile")` just before `if is_link(root / "profile"):`. The tool then lists `profile/` itself, through the link, before it refuses it. `os.scandir(path=...)` and `open(file=..., mode='rb')` do the same. I ran the same three definitions (`scripts/defs_r1c.py`) against the one test that holds this, `test_profile_itself_a_junction_to_a_directory_outside_the_tree_is_refused_by_name_and_nothing_behind_it_is_read`.
  - On main (8fe0268) with main's test, all three were KILLED, by `[--check]`.
  - On the packet with the packet's test, all three SURVIVED ("2 passed").
- **Cause (READ).** Main's `watch_reads` noted `a[0] if a else next(iter(k.values()), None)`. P4.2's `watch_below` notes `a[:2]` only (`tests/p4/p4_helpers.py:667`). `spy_missed` makes every call positionally, so its control cannot see the loss.
- **It is wider than that one test.** At C1's own seven places I made `drift()` (and the write branch, before its removals) ask the host about a rendered path behind the link and throw the answer away. Only the spy can kill that (`scripts/defs_r1b.py`, 64 mutants).
  - 16 calls written positionally (the ruling's and others), at two sites: 32 of 32 killed.
  - The same calls with the path given by keyword: 12 of 14 survive. They are `os.stat`, `os.lstat`, `os.listdir`, `os.scandir`, `os.access`, `os.path.exists`, `os.path.isdir(s=)`, `os.utime`, `os.path.realpath`, `open(file=)`, `io.open(file=)`, and `os.stat(path=)` in the write branch.
  - Names bound before the spy goes in: 9 of 10 survive (`from os import stat`/`listdir`/`scandir`/`access`, `from os.path import exists`/`isdir`, a module-level `_x = os.stat`, `from io import open`, `_io.open`).
- **The claim it breaks.** `docs/P4.md:58` says "a spy on every call of the standard library that could follow a link or read through it finds none". The docstrings of `watch_below` and `test_p4_tree.py` say much the same. The blind spots the builder lists (a DirEntry, a handle already open, ctypes, a process) leave these two out.
- **The tool itself is right.** My own spy (`scripts/spy_child.py`) patches every path-taking function of `os`, `nt`, `ntpath`, `open` and every `Path` method, positional and keyword, before the tool is imported.
  - It sees 3 to 15 calls below the link from main's tool in `--check` at the seven places.
  - It sees 0 from the packet's tool at all seven places and at `profile/` itself, in both modes, with the same exits.
- **To mend.** Note the keyword values too (`for p in (*a[:2], *k.values())`). Make `spy_missed` call each wrapper by keyword as well. Either list names bound early among the blind spots or drop "every".

**D2. Prose: limit 24 says two things that are not so.** It is at `qro/p4_profile.py:258-268` and so `profile/README.md:83`. The second statement is pinned word for word by `test_p4_profile_crate.py`.

- **"a number at a term that takes none is refused `spelling` too".**
  - I put an integer of 20, 4,300, 4,301 and 5,000 digits at each of the 42 leaves of the fixture's `@graph` and read it with the reader (`scripts/probe_digits.py`).
  - At 4,301 and 5,000 digits, `spelling` at all 42 leaves.
  - At 20 and 4,300 digits, `spelling` at 34 and **`graph-form` at 8**: the descriptor's `about` and `conformsTo` ids, and the two Profile entities' `name` and `version`.
  - The point of the limit holds: no crate reaches the evaluator with such a literal, because `json.loads` refuses it first, everywhere. The refusal name does not hold.
- **"a number past 2^63 - 1, so one of more than 19 digits".** 2^63 - 1 has 19 digits, and 9223372036854775808 is past it with 19. The implication runs the other way.
- **To mend.** Say that every number of more than 4,300 digits is refused `spelling` wherever it stands. Say that a shorter one past 2^63 - 1 is refused at step 1 too, by `spelling` or `graph-form`. Let the eval test take more than two terms.

## What I checked and found right

- **The freeze.**
  - SHA256SUMS.txt begins 2abb3962, and `sha256sum -c` over the tree passes 411 of 411.
  - Over the builder's worktree, read only, it passes 411 of 411 with no file outside the list.
  - The ledger, brief and lead's ledger hashes are as the brief says.
  - `diff -rq` against main shows exactly 16 files, none added or removed, all P4's.
  - No CR byte in any of them. Non-ASCII counts are main's own.
- **The runner.** The packet committed as 08d6764, full command through `sbx-mid.sh`, run `20261031-060117-9957-08d6764`: 22 passed, 0 failed, 2 skipped by name (p1-crates, p2-crates), exit 0.
  - p4 990 passed, p4-shacl 236 passed, so the engine agrees with the evaluator.
  - Stage seconds sum to about 1,320 s, beside my own mutation passes.
  - I did not run the quick budget alone, because its stages are a subset.
  - `pytest tests/p4` with a basetemp of my own: 990 passed.
- **profile/.** `gen_profile.py --write` in a fresh copy holding only `qro\`, the tool and P0's context gives a `profile/` identical to the packet's, 12 files, byte for byte. Only the four banners, limit 2, the new limit 24 and the Profile Crate's digests moved. I re-measured limit 2 with the engine run as the stage runs it: 0, 94, 112 and 527 results, and every type and triple the text lists is right.
- **The host facts and ruling 1.** With real junctions, each taken away by making its target again, I measured what the page now says in every state.
  - A junction at `context.jsonld` whose target became a file is exit 1 "cannot be read (OSError)"; `open` raises OSError, errno 22.
  - At `profile/` it is exit 1 "is missing".
  - Below `profile/` it is exit 3 `Unlistable`.
  - `os.access(F_OK)` is True for a dangling junction in four spellings.
- **"Nothing else moved."** I ran main's tool and the packet's, each on its own profile, over 31 tree states (`--check`, `--write`, `--check`), comparing exits, stdout, stderr and the tree left.
  - 22 states are identical.
  - Nine differ: C1 (2, the one line the page names), C4 (2, the clause), C6 (2, the escape), and 3 that no ruling names (note 1).
  - No exit differs in any state.
- **The closure.** I ran the sixth verifier's 12 and the seventh's 147 and 16 against the packet's tests (`scripts/defs_r1a.py`). Of 187, 180 were killed and 7 survive, all `os.access` (note 2). A08 is killed by its new test. The builder's other three "equivalents" are equivalent: `directories()` including "." (no rendered path is "."), and `escape` of a rendered path (ASCII, no backslash). G11 is note 4.
- **Rulings 2 to 12** are each met by the test or the text the builder names, and the tests hold what their names say.
  - One reach point: the test of limit 2's lists pins the words and not the engine's output. The builder says so in the limit's text, and I re-measured the lists.
  - `--help` prints the description, both modes and the exits, also under `-OO`.
  - The exit-1 sentence is the same in `--help`, the docstring and the page.
- **Junctions.** A passing run leaves 0 links in my own basetemp. No failing run stranded any, live or dangling, in the 187, 64, 20 and 4 mutant runs above; the last four ran every failing test (27, 40, 23 and 128 failures). My final scan of my directory found 0 links.

## Notes (below the bar)

1. **Code, text only.** A directory spelt in another case at the place of a rendered file is now told "`missing; run --write`". Main said "`is a directory, not the file its definition renders; run --write removes it`". Examples are `profile/readme.md/` for `README.md` and `PROFILE.TTL/` for `profile.ttl`.
   - `directories()` compares exact spellings, and `is_dir()` did not, on this case-insensitive host.
   - No ruling or page sentence names it, so the ruling's "say what changes in a line" is incomplete.
   - Exit and `--write` are the same. A `fold` would keep the old line.
2. **Gate.** The seven `os.access` survivors are equivalent here and only here. A tool that decided by `os.access` would break on a host where it answers no, and no test would show it. Running the told tests with the answer both ways would kill them.
3. **Gate.** `--help`'s layout is not held (my B01: `RawDescriptionHelpFormatter` removed; B04: wrapped at 20), because the test normalises white space. Cosmetic.
4. **Gate.** G11, the guard's scan of `tests/p4shacl`, is held by no planted module there. It is equivalent today.
5. **Prose.** The banner "descriptor, entity and profile-entities, all shapes of must/1_structure.ttl" can be read as "the file holds only these". The file holds nine, and its line 2 says so. "three of the file's nine shapes" would not mislead.
6. **Prose.** `--help`, exit 3: "and never a verdict; so is any other file it cannot read" does not parse.
7. **Prose.** Docstring and page: "The tests make no such junction: it could not be taken away again". It can, by making its target again (CLAUDE.md item 10); I did.
8. **Prose.** The `test_p4_tree.py` docstring says "here no call is told, so none can be missed". `os.unlink`, `os.rmdir` and `os.access` are told. The docstring of `dangling_link` and the page say so exactly.
9. **Other (BELIEVED, not run: no symbolic link can be made here).** On a host with symbolic links, `os.walk` calls `DirEntry.is_dir()` on a link, which follows it. That is a stat of where the link points, though not of anything below it. "Never read through" is then true as worded ("below") and no more.
10. The builder's three stand-in differences are as it says.
    - `os.unlink` raises PermissionError where this machine raises FileNotFoundError.
    - The entry's `stat()` has zero times.
    - The NotADirectoryError variant tells four calls and not `open`, where the machine's `open` raises OSError 22.

## What I did not do

- I ran no POSIX host, no host that opens a dangling junction, no Python but 3.12.15, and no symbolic link (WinError 1314).
- I did not re-run the builder's 307 mutants or its 140 earlier-round ones. I ran the two earlier verifiers' 187 and 88 mutant runs of my own (K 64, PK 10 on each of two trees, L 4), plus the spy, differential and probe runs.
- I read the diffs of every changed file whole and the tests around them. I did not read the unchanged parts of the test files line by line.
- I did not read `docs/VALIDATION.md` for the merge entry's wording.
- I ran the engine only through the stage and through the builder's probe, which I read first and which follows the design's rules for it.

## My slips

- **A file in the owner's Temp folder, still there.** By a redirect in my first command I wrote a sorted list of the frozen tree's file names to `<home>AppData\Local\Temp\__nothing` (17,689 bytes). I did not delete it, because the rules allow deleting only inside my directory. It holds repository file names, record names among them. Please remove it.
- **Python outside the launcher.** Twice I sent an empty heredoc to the plain shell's `python`, with no program and no write. `python3` was not found three times.
- **Junctions from a crashed spy run, removed.** My first spy run crashed (recursion in my wrapper) after making 16 live junctions in my directory. I found them with a scan and removed each by `os.rmdir` while its target was there. The last scan found none.
