# P1.2 verifier, round 6: report

## Verdict: NOT READY

I found two defects in what the code does. Both are in `check_moth`, the check that a `--moth` checkout is "clean at 3a73823". Everything else I attacked held: the cleanup, the out guard, round 5's three fixes, the derivation of every CHECKED value, the generator's guards, the real crates and the seven controls. Neither defect is a wrong acceptance by the checker, and neither touches the real crates.

Labels: MEASURED means I ran it. The script is named, and all are in `<home>AppData\LocalLow\qro-sbx\p12-r6\s\`. READ means I read the code. BELIEVED means neither. All code ran through sbx.sh and the runner through sbx-mid.sh. IBM job ids are masked. The harness refused a separate report file, so this message is the report. My working notes are `<scratch>\verifier-P12-r6\check\notes.md`.

## Defects (both code)

### D1. git's output is decoded with the locale's code page, so a modified checkout gives exit 3 and a traceback where it must give exit 2

- **Cause (READ).** `p1_adapter._git` calls `subprocess.run([...], capture_output=True, text=True)` with no encoding or errors.
  - On this host the preferred encoding is cp1252, which has no byte 0x81, 0x8D, 0x8F, 0x90 or 0x9D.
  - The decode fails in `subprocess`'s reader thread, `run` returns `stdout=None`, and `r.stdout.strip()` raises `AttributeError`.
  - `_git` catches only `FileNotFoundError` and `OSError`, so `main` answers exit 3.
- **Fault that shows it (MEASURED, `e12_d1_process.py`).** The run is a process, on a real clone of moth-quantum at 3a73823, with no patching of the adapter.
  - A `.gitconfig` in a home directory of mine sets `core.quotePath = false`, a very common setting. The clone holds one untracked file, `docs/&lt;U+0141&gt;x.txt`.
  - `python -m qro.p1_adapter atlas --moth &lt;clone&gt; --out &lt;new&gt;` gives exit 3 and 14 lines on stderr. They are the thread's traceback, `UnicodeDecodeError: 'charmap' codec can't decode byte 0x81`, and `FAILED: the adapter itself failed, AttributeError: 'NoneType' object has no attribute 'strip'`.
  - The same file under the default git config gives exit 2, `has changes that are not committed`. An ASCII untracked file under the global setting also gives exit 2.
  - In process on a toy repository (`e5_gitenc.py`), U+0141 and U+0150 fail. U+00E9 and CJK U+4E2D U+6587 decode and give exit 2.
- **Reach.**
  - The real checkout at 3a73823 has 13,412 tracked names and none is non-ASCII (`e6_names.py`). An honest build is not affected.
  - The input is a modified checkout (a changed or untracked non-ASCII name) under `core.quotePath=false`.
  - git's stderr is decoded too, so a git error quoting a path with such a character takes the same road (BELIEVED, from the same code).
- **It contradicts** the docstring and the page, which put a checkout the adapter will not use at exit 2, and the contract of one line. No test sets `core.quotePath`.
- **Closure (MEASURED, `e20_d1_trialfix.py`, in my private copy `mut\b`, never the tree).** Decoding git's bytes as UTF-8 with `errors="replace"` makes U+0141, U+0150 and the ASCII case all exit 2.

### D2. An untracked file that git ignores is not seen, though the page says untracked files are seen "whatever the checkout's own settings say"

- **Fault (MEASURED, `e14_ignored.py`, same real clone).** I wrote a copy of a real kingston snapshot into `docs/records/2026-10-05/ibm/ibm_kingston/`. Its `last_update_date` was moved an hour and the file was named for the new stamp. I listed it in `.git/info/exclude`.
  - `git status --porcelain --untracked-files=all` prints nothing.
  - The adapter gives exit 0, `BUILT ibm: 1074 files` (one more than the honest 1,073), identity `2c5b1b3b...`. The checker ACCEPTS that crate, extra snapshot included.
  - So the adapter built from a checkout that is not clean at 3a73823.
- **Cause (READ).** `check_moth` runs `git status` without `--ignored`. `.gitignore`, `.git/info/exclude` and the user's global excludes are "the checkout's own settings", and an ignored file is an untracked file.
  - The page's sentence and the test name `test_an_untracked_file_is_seen_whatever_the_checkouts_own_settings_say` claim more than the test holds. It sets only `status.showUntrackedFiles=no`.
- **Reach.**
  - Only a file that matches a layout passes. Any other ignored file (`*.bak`, `.DS_Store`) is refused G12, exit 1.
  - The crate is self-consistent, so the checker's invariant holds. What fails is the adapter's documented precondition.
  - `--ignored` cannot be added wholesale, because the real checkout holds ignored directories (`.atlas/`, `responses/`). The check has to be limited to the paths the plan reads.
- I rank D2 below D1. The lead may rule it a note.

## What held (MEASURED unless marked)

### Round 5's three fixes
- **Records' check from an explicit stack.**
  - `_unencodable` agrees with a recursive reference on 30,000 random documents, 18,947 of them with a lone surrogate in a key or a value. The place is the same and so is `rec.parse`'s message (`e15_unencodable_diff.py`, 0 mismatches).
  - As processes, a surrogate at depth 10, 500, 980, 1,000, 1,500 and 2,900 in the IBM job line is exit 1 with the field named. The encodable control at 1,500 is exit 0 (`deep_surrogate_proc.py`). The Atlas path at depth 10 and 1,000 is exit 1 (`deep_atlas.py`).
  - `json.dumps`, `==`, `record_digest` and `options_digest` admit more depth than the reader does (3,001 and 2,999 against 2,996 and 2,994), so there is no RecursionError window at the reader's limit (`e1_depth_prims.py`).
  - A member nested at the reader's limit, spliced into the text of every small JSON file with digests resealed (`f4_boundary.py`), gave 650 trials with no crash.
  - A lone surrogate in a string leaf and a key of every class of the closed forms (`f5_surrogate.py`) gave 1,606 trials with no crash.
- **Degenerate `--out`.**
  - My own sweep (`e16_outs.py`) used 41 spellings inside the sandbox and 33 outside, with the builder's simulated unreachable host for the network forms. Every exit is 0 or 2, and a refused build leaves nothing.
  - It covers `\\`, `\\server`, `\\?\`, `\\.\pipe\`, `\\?\UNC\`, `<a home path>...`, a trailing space (exit 2), a trailing dot (built: Windows drops it), ADS (exit 2), `::$INDEX_ALLOCATION` (built), CON, COM1 and aux.x (built on this host), a lone-surrogate name (built), a 256-character component (exit 2) and a 1,000-character path (built).
  - The exit codes are the same on Python 3.13.5.
- **Inputs the host will not let the adapter look at.** I tested against real NTFS deny ACEs, not the simulated hosts (`e7_acl.py`, the adapter as a process, on copies in my directory).
  - A denied directory that the plan lists gives exit 2 with the input and the place named, and nothing left. The directories were the IBM records directory, a device's run or bundle directory, and `--records`' two read directories.
  - An unreadable record the build copies, the LICENSE, or a job line a slice reads gives exit 3 with nothing left, as the page says.
  - The simulated hosts therefore hold what the tests say of real ones. Three rows of that script said FAIL, and all three were my wrong expectations. A deny of read-attributes does not make stat fail when the parent can be listed, and a day directory that nothing lists is not an error.
- **The memory test's one failure.** I could not reproduce it. I ran it 8 times, then 45 times under `PYTHONHASHSEED` 1 to 45 beside two other heavy processes, and I repeated the whole `tests/p1` directory (1,776 passed in 325 s). The failing difference, 976,165 bytes, is almost exactly eight times the 120,000-byte padding, as if all eight parsed records were alive at the peak. BELIEVED: leftover state in that process or the host, not P1.2's code. I cannot say more.

### Rounds 1 to 4, and the cleanup
- Round 4's out-guard tests aim at directories of their own, and the p1-crates test calls `check_out` alone and builds nothing (READ).
- The earlier verifiers' cleanup attacks, rerun on this tree:

| script | result |
|---|---|
| `ca_inject` | 0 of 80 failed |
| `cb_foreign` | 0 of 43 |
| `cc_fail` | 0 of 9 |
| `cd_process` | 0 of 37, exit codes 0, 1, 2 and 3 and never 120 |
| `h5_prejunction` | 0 of 18 |
| `a1_outs` | 0 of 32 |
| `h6_open_handle` | leaves the manifest and its five ancestors, C22's case |
| `h4_late_oserror` | exit 3 with the world restored |
| `a2_swaps` | one row fails, S2, the check-to-unlink window that limit 22 states |

  The same on Python 3.13.5.
- The shared temporary folder holds 133 links, none live. P1.2's one junction-making test accounts for 13, unchanged by my runs (`e11_links.py`). The rest are P0's format tests'. No `p1-real-*` or `p1-twin-*` directory is left behind.

### The generator and the guards
- **No CHECKED value is copied.**
  - By audit events it opened 72, 30 and 1,072 files of the twin, Atlas and IBM crates and never `ro-crate-metadata.json`. Its output is identical with the descriptor removed, garbage, or with every CHECKED term changed (`t1_open.py`).
  - With every guard off, a sentinel from `commitment_of`, `claims`, `link_for`, the rule table's name or the file hash is the value of every term it makes (`t2_sentinels.py`).
  - 45 edits of the real IBM crate's metadata over all 15 CHECKED terms are all refused (`meta_sweep_real.py`).
- **Generator against the whole checker.**
  - Type poison (`f2_typefuzz.py`): the first leaf of every class of every small JSON file replaced by `None`, `true`, `-1`, `1.5`, `""` or `[]`, digests resealed to a fixpoint. That is 5,253 trials, 2,415 on the twin and 2,838 on Atlas. Where the generator accepted, I wrote the descriptor as the adapter writes it and ran the whole checker. No crash, and no crate the generator accepts and the checker refuses.
  - Two were accepted by the generator and refused by the writer (qiskit `""` and the Atlas vector's `job` `""`), exit 1, as the page says.
  - File level (`f3_files.py`): each file deleted, emptied, given another file's bytes with digests resealed, or given an extra copy. That is 404 trials. All extra copies are refused G12, and nothing crashes. Five twin deletions are note N1.
- **Each guard.** I made the condition True at each of the 78 `_hold` sites of `p1_generate.py` in turn (`m1_guards.py`). 73 are killed by `test_p1_generate.py` and `test_p1_atlas_generate.py`, and the seam's four by `test_p1_seam.py`. One survives, `_reads`' "more than one MANIFEST" (line 617), which can never fire. The layout admits one MANIFEST path, so it is dead code and not a gap.

### The freeze, the runner, the real crates, the controls
- **Freeze.**
  - The 14 packet digests I checked equal the brief's. `SHA256SUMS.txt` begins `a905c847e9d00541`, and `sha256sum -c` gives 368 of 368.
  - The worktree equals the packet's tree file by file and holds no other file.
  - Against 37640f0 the packet adds 77 files and changes two: one bullet in `docs/README.md` and `GENERATORS` in `qro/register_p1.py`. Its text files are LF.
  - The twin's 56 files (828,488 bytes) each equal `git cat-file blob 3a73823:&lt;path&gt;`, and none is an Atlas response.
- **Full runner** through sbx-mid.sh on my committed copy `dae0f45` (run `20261031-021808-4330-dae0f45`): 19 passed, 0 failed, 5 skipped by name (p2, p4, p2-crates, profile, p4-shacl).
  - p1 has 1,776 passed (223 s), p1-crates 41 (231 s), control-tests 39. The copy was clean afterwards.
  - moth-quantum's `.git/index` is still dated 2026-10-15 20:43:39, and its HEAD is 3a73823 and clean, after the runner and every build.
- **Real crates** (the adapter as a process, then `python -m qro check` as a process, then again on Python 3.13.5):

| crate | files | bytes | identity | checker |
|---|---|---|---|---|
| IBM | 1,073 | 53,269,160 | `8ec4dc39df52c0dc9a0fc84406603d234308ef967aa1b5902a3d97f8af974b9a` | ACCEPTED |
| Atlas | 31 | 4,975,638 | `f9c1a259786e3e9a98423721b5b2c275b8b38e3d7b0339f01423d01cb793f025` | ACCEPTED |

  - The Atlas crate built from my clone has the same identity.
  - The page's counts hold. For IBM: 1,072 files and 52,506,692 bytes besides the descriptor, 1,380 entities, longest path 77 (ten at 77, eight at 76), 161 mentions, 12 snapshots and 995 plain Files. For Atlas: 30 files, 4,946,204 bytes and 63 entities. For the twin: 73 files and 107 entities.
- **The seven controls** come out as section 11 says in `controls-run`: 16 of 16 built controls.
  - `job-reattributed` is refused `commitment` and `bits-mirrored` `known-answer`.
  - `calibration-late` and `calibration-gap` are refused `calibration-link`.
  - `qpy-only`, `calibration-restamped` and `shot-moved-resealed` are accepted.
- **The two changes the lead did not ask for.** `GIT_OPTIONAL_LOCKS=0` holds, since the index time did not move. A foreign file where the build writes is exit 3 with the file left (F5).

## Notes (they do not block)

### Code-adjacent
- **N1. A slice that lacks a file a carried job's commitment binds builds, exit 0, a crate the checker refuses** (`e18_incomplete_slice.py`).
  - G1 holds a bundle file "where present". A copy of the twin without `coherence-xx.qasm` gives `BUILT ibm: 72 files`, exit 0.
  - `python -m qro check` on that crate says `REFUSED commitment at #pub-&lt;job&gt;-0 qro:record: no file of the crate has the circuit_sha256 the commitment binds`.
  - The same happens for `coherence-xx.qpy`, `coherence-yy.qasm`, `coherence-yy.qpy` and sheet-02's `known-answer.qpy`.
  - The checker never passes the crate. A full checkout cannot lose a file without `git status` saying so, so this is slice-only. The adapter does not run the checker on what it builds. I leave it to the lead, who could make it a guard or a last step.
- **N2.** `--slice` given twice is accepted silently, though other options say "given twice". Harmless.

### Test reach, where the code is right
- No test sets `core.quotePath`, a non-ASCII name in the checkout, or an ignored file. D1 and D2 are those gaps.
- The test named for untracked files "whatever the settings say" holds one setting.

### Prose
- The exit-3 list on the page and in the docstring does not name git's output being undecodable. After D1 it is in the wrong list.
- The page's "whatever the checkout's own settings say" is false for ignored files (D2).

### Other
- Real Atlas job id literals: `tests/p1/test_p1_records.py:350` and P1.1's `tests/p1/test_p1_graph.py:141` (`e10_ids.py`). Every other UUID literal in P1.2's tests is synthetic. The lead left this as Logan's to rule on.
- P0's format stage (37640f0's tests) strands dangling junctions in the shared temporary folder at each run. My runner run added some, as the earlier verifiers' did. P1.2's tests add none.

## What I did not do
- The merge onto main (83503b0 and P0.8's d98295e, with P2.1 and P4 merged) and P2's real `qro/p2_measures.py`. I did not read or run them. The seam was held to ledger-P2.md section 9 by reading, and by the earlier verifiers' stand-in. Main has moved in `qro/checker.py`, `spelling.py`, `reader.py`, `canonical.py`, `vocabulary.py` and `docs/README.md`.
- The quick budget alone, P1.2's 364 mutants, or a leaf-by-leaf sweep of the 1,380-entity IBM crate.
- A host with long paths off, a non-Windows host, a host that opens dangling junctions, a FAT or exFAT volume, a `subst` drive, a OneDrive folder, or Python 3.14.
- A real network share. The network spellings ran against the builder's simulated host.
- Python 3.13.5 ran only the adapter and the earlier verifiers' scripts. It ran through sbx.sh without the audit hook, so the low-integrity label was the only fence. I did not run pytest on it.
- I repeated none of the earlier verifiers' 12 random honest slices (G9's "refuses nothing honest" rests on them).

## Disclosures
- I ran `git status --ignored` in the real moth-quantum checkout to read its ignore rules. It listed names of ignored files under `.atlas/`. I opened none, and two Atlas job UUIDs appeared in my console output. I did not repeat it, and the index is unchanged.
- One of my scripts (`e10_ids.py`, unfiltered) printed IBM job ids from file names under `records/2026-10-14/` to my console. They are in no note or report of mine.
- My first runner command ran past ten minutes and the harness moved it to the background. It finished normally. My long sweeps ran as shell children of my commands, not as detached processes.
- I wrote two helper file lists to my check directory with shell redirects (`wt_files.txt`, `tree_files.txt`). I appended to `notes.md` with shell redirects as well.
- My deny ACEs on copies in my directory were removed in a `finally`, and the one I set by hand (`acl\d1`) lists normally again. I made no junction.
- My directory holds a few GB: tree and mutant copies, a clone of moth-quantum, crates and logs. It sits wholly under `<home>AppData\LocalLow\qro-sbx\p12-r6\`, and one world directory is left from an early harness crash, `worlds\f2t_a`.
