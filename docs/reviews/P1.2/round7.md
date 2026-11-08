## Verdict: READY (on the relaxed bar)

I found no defect in what the code does that blocks under the cap's definition.

- **Round 6's fixes hold.** D1 and D2 are fixed under every route I could build, on the real moth-quantum, on fresh clones and on toy checkouts. N1 and N2 hold. The builder's five readings are sound.
- **No wrong exit code or crash.** I tried about 100 odd inputs and states, and none gave a wrong exit code or a traceback.
- **Cleanup holds.** The cleanup removed or wrote nothing it had not made. The one failing row is limit 22's stated window.
- **No wrong acceptance by the checker.** The generator copies no CHECKED value.
- **Two items I did not count as blocking:** a false sentence on the page (F1) and a gap in test reach (N2). F1 is the one I would send back if the lead counts the *missing-file* direction of D2's class.

Labels: MEASURED names its script (all in `<home>AppData\LocalLow\qro-sbx\p12-r7\s\`). READ means I read the code. BELIEVED means neither. IBM job ids are masked. The harness refused a separate report file, so this message is the report. My working notes are `SCRATCH\verifier-P12-r7\check\notes.md`.

## Defects

None. Nothing about code, gates or prose blocks.

## Notes

**F1. Prose, with a code closure if the lead wants one: a lying `core.fsmonitor` hides a deleted file.**
- **The sentence.** `docs/P1.md` says "A checkout cannot lose a file without `git status` or `git ls-files -v` saying so." That is false when the checkout's own config sets `core.fsmonitor` to a hook that reports no change.
- **The fault (MEASURED, `f1_fsmonitor.py` on a toy; `f2_fsm_real.py` on a fresh clone, through sbx-mid.sh because git runs the hook through sh).**
  1. Set the hook to `printf 'lie1\0'`.
  2. Run `git status` three times.
  3. Delete one of Quantum-Film's five snapshots.
  4. `git status` is empty and `ls-files -v` marks nothing.
  5. The adapter exits 0 with `BUILT ibm: 1072 files, 52527047 bytes, identity 802465229e52…`; the honest crate has 1,073 files.
  6. `python -m qro check` ACCEPTS it.
- **Why I did not block.** Every file the build takes is still 3a73823's own, and a changed or added file under the same hook is refused. The crate names no source commit and makes no claim of completeness. Limit 4 already concedes that a crate without one of those five snapshots is accepted. The setting is a lying git, not an ordinary one.
- **Closure.**
  - Have `head_tree` list the entries under the directories the plan walks, and refuse a tracked file the plan did not take.
  - Asking `ls-files -v -f` would also mark fsmonitor-valid entries, but it would mark every file of an honest checkout that uses the built-in FSMonitor.
  - At minimum, restate the sentence at the merge.

**N2. Test reach, where the code is right: the hold's wiring in `build` is pinned for three classes of file only.** MEASURED with my harness `mut7.py` and mutants7a to 7c, each mutant skipping the hold for a class of file.
- **Killed:** the hold off altogether, LICENSE, the Atlas day files, and the snapshots (`properties-*`).
- **Survived the round-6 adapter tests:** sheet files, QPY files, job lines, the vector, bundle files, run files, qasm files and prediction files.
- **Survived the whole 188-test adapter file:** sheet files, QPY files, and "hold applied to LICENSE, snapshots, Atlas p3 files and the vector only".
- **Discarded:** two of my mutants were malformed by operator precedence and are not counted.
- **Why the stage cannot kill them.** The p1-crates real-checkout test asks the rule of 960 honest files and cannot.
- **A test recipe.** In the committed twin checkout, flip one byte of a file of each layout class, keeping size and mtime. `git status` says clean on this host (`b3_forged_stat.py`), and the build must exit 2.

**N3. Prose, minor.** The adapter's module docstring says "Clean is two things" and then lists three clauses: status, `ls-files -v`, and every file taken.

**N4. Other.**
- **What I saw.** moth-quantum's `.git` directory mtime reads 06:58:25 today, the end of my runner's last stage, `instruments`. Its index (2026-10-15 20:43:39), HEAD and status are unchanged.
- **Not P1.2's.** Study QRO-0's instruments run `git status --porcelain` there without `--no-optional-locks`. The adapter and the p1-crates adapter tests do not move the mtime (stat before and after). I believe the instruments stage is the cause.

**N5. Behaviour worth knowing; both are documented.**
- A cone-mode sparse checkout that holds every file the plan reads is still refused. `ls-files -v` marks 269 files `S`, and the exit is 2 naming `.github/workflows/pages.yml`.
- A junk file ignored in a plan directory (a `desktop.ini`, say) now exits 2 naming the file. It used to exit 1 by G12.

## What held

**Freeze and files**
- `SHA256SUMS` begins `3f319865444079bc`. `sha256sum -c` gives 369 of 369 over the packet tree and 369 of 369 over the worktree (read only).
- Against 37640f0 the packet adds 78 files (22 of P1.2's, 56 twin) and changes two: one index line in `docs/README.md`, and `GENERATORS` in `qro/register_p1.py`. All are P1.2's.
- Against the round-6 packet, 5 files changed and `p1_pinned.py` is added.
- The changed files hold no CR, no byte above 0x7F, no home path, address, key shape or job id.
- The twin's 56 files each equal their blob at 3a73823.

**Runner (sbx-mid.sh, committed copy 8b8ae2c)**
- Run `20261031-064140-1127-8b8ae2c`: 19 passed, 0 failed, 5 skipped by name (p2, p4, p2-crates, profile, p4-shacl).
- p1: 1,831 passed in 356 s. p1-crates: 42 passed in 300 s. No stage log holds "QRO sandbox".
- `test_p1_adapter.py` alone under sbx.sh at low integrity: 188 passed.
- P1.1's memory test passed 12 of 12 with `PYTHONHASHSEED` 1 to 12. I cannot say what failed once.

**Real crates**
- IBM: 1,073 files, 53,269,160 bytes, `8ec4dc39df52c0dc…`. Atlas: 31 files, 4,975,638 bytes, `f9c1a259786e3e9a…`.
- Both were built from the real checkout and from a fresh clone, and the checker ACCEPTED both clone crates.
- The same identities came from:
  - two depth-1 clones made under `core.autocrlf=false` and `core.eol=crlf`;
  - a depth-1 clone and a git worktree;
  - a checkout under a path with spaces and U+0141 U+0150;
  - `--moth` spelt relative, with forward slashes, with a trailing separator, as `.`, with the `\\?\` prefix, and in upper case.
- The two crates built from the real checkout and from the clone differ only in the descriptor's two header lines.
- The page's counts hold (`g1_counts.py`, `g3_bytes.py`), and the plan leaves out only the four probe files.
- The p1-crates adapter tests, including the 930 and 30 file hold, pass with the fresh clone as the checkout.

**D1 (`a1_names.py`, `a2_homecfg.py`, `j1_brokengit.py`)**
- With `core.quotePath` false and true on a fresh clone, an untracked file named with U+0141, U+0150, U+00E9, CJK, U+1F600, a combining mark, a space plus U+0141, RTL, NBSP, NEL, LS or a BOM gives exit 2, one line, no traceback, and nothing made (66 rows).
- Intent-to-add plus assume-unchanged names, which `git status` does not show, give exit 2.
- The sixth verifier's own scenario (a `.gitconfig` in a home directory with `quotePath=false`) gives exit 2.
- Thirteen broken git states (truncated or empty index, garbage HEAD or config, empty `.git`, bare, `core.worktree` elsewhere, a missing tree object, an unborn branch, and others) give exit 2 or a benign build. None gave exit 3.
- Against the round-6 adapter, 43 of the 58 selected new tests fail. The D1 process tests fail with exit 3 and "AttributeError: 'NoneType'…", which is the reason D1 named.

**D2 (`b1`, `b2`, `b3`, `b4`, `c1`, `j2`)**
- **Ignore rules.** An extra snapshot or Atlas file ignored by `.git/info/exclude`, `core.excludesFile` or a nested `.gitignore` gives exit 2, names the file, and leaves nothing.
- **Attributes.** `eol=crlf` on LICENSE, an IBM record, the vector or two records, and `working-tree-encoding=UTF-16LE`, with `git status` clean, give exit 2 "not moth-quantum's bytes". The plan that does not take the file builds as ever.
- **A clean/smudge filter driver** on LICENSE gives exit 2.
- **Stat forgery.** One byte flipped with size and mtime kept: `git status` said clean, and the adapter exits 2. This is stronger than the ruling asked.
- **Submodule.** A walked directory that HEAD's tree holds as a gitlink: `git status` is blind, and the build exits 2 naming the file.
- **Links and cleanup.** The link, executable and `git replace` cases are in the suite and pass. The hold refusing the 1st to 56th file into fresh-nested, existing-empty and parents-partly-made outs restores the world exactly. A foreign file dropped into a directory the build made stays with its directories and nothing else.
- **N1 and N2 as processes** (`d1_n1n2.py`). The slice without `coherence-xx.qasm` builds, and the checker refuses `commitment`. `--slice` twice, `--moth` twice and `--out` twice give exit 2 with nothing made.

**Rounds 5 to 1**
- A lone surrogate nested 10 to 2,900 deep gives exit 1 with the field named, and the encodable control at 1,500 builds (`deep7.py`).
- The sixth verifier's out-spelling sweep, retargeted, gives "unexpected: 0".
- A dangling junction inside a walked directory gives exit 2 naming the place (`i1_dangling.py`).
- Nineteen odd `--moth`, `--records` and `--out` values give exit 1 or 2 (`k1_inputs.py`).
- Twelve random honest slices of the real records built and were ACCEPTED (`slices7.py`), so G9 refuses nothing honest in that sample.
- The fourth verifier's cleanup scripts, retargeted:

| script | result |
|---|---|
| `ca_inject` | 0 of 80 failed |
| `cb_foreign` | 0 of 43 |
| `cc_fail` | 0 of 9 |
| `cd_process` | 0 of 37 |
| `h5_prejunction` | 0 of 18 |
| `a1_outs` | 0 of 32 |
| `h4_late_oserror` | exit 3, world restored |
| `h6_open_handle` | the C22 case |
| `a2_swaps` | 1 of 37, S2, limit 22's window |

- The junction-making adapter tests left the shared pytest temp folder's link count at 147 before and after. The 13 stranded junctions there are older runs'.
- The adapter holds no recursive delete, only `os.unlink` and `os.rmdir`. The three `atexit` rmtree calls remove `mkdtemp` directories.

**Generator and controls**
- An audit hook on `open` shows the generator never opens `ro-crate-metadata.json`, on the real Atlas and IBM crates.
- **Atlas sweep** (`m1_meta.py`): 752 edits of every non-@id term, against the whole checker. None of a non-header term was accepted: 36 were list reorderings the canonical writer sorts back, and 1 was a header term.
- **Twin sweep:** 1,229 edits, 363 refused by step 9, 47 no-ops, and 1 accepted header term.
- The seven controls come out as section 11 says: 16 of 16 built controls in `controls-run`.

## What I did not do
- I did not repeat the real-ACL deny tests. I relied on the sixth verifier's run for "the simulated hosts hold what the tests say of real ones", read `p1_hosts.py`, and measured one real refusal that needs no ACL.
- I did not try a UTF-8 code-page host, a non-Windows host, git older than 2.29, Python 3.13 or 3.14, a real network share, or a partial clone.
- I did not run the merge onto main or P2's real `qro/p2_measures.py`, the quick budget alone, P1.2's own 26 mutants, or a leaf-by-leaf sweep of the 1,380-entity IBM crate.
- Both metadata sweeps stopped at my time limits, so entity coverage was partial.
- I used my own harness `mut7.py`, not `hm_t.py`.

## Disclosures
- **Printing slips.** A controls-run log tail printed three IBM job ids unmasked to my console. Two metadata-sweep outputs printed truncated Atlas job-id entity @ids. None is in a note or this report.
- **The real moth-quantum.**
  - Read only: git with `GIT_OPTIONAL_LOCKS=0`, plain reads of `.gitattributes`, `.gitignore`, `.git/info/exclude` and `.git/config`, and adapter builds.
  - Never `git status --ignored` there.
  - The runner's own `instruments` stage ran git there, as every full run does.
- **Deletion.** I used `shutil.rmtree` only in my scripts, under sbx.sh, on directories inside my own sandbox. I ran `rm -rf` only on literal paths in my directory.
- **Junctions.** I made junctions only in `i1_dangling.py`, removed with their targets made again first. A scan of my whole directory finds 0 links.
- **Other.** The first `cd_process` run showed 4 failed rows because I had not copied the fourth verifier's seam stand-in. After copying it into my own `tree-seam` copy, all 37 rows pass.
