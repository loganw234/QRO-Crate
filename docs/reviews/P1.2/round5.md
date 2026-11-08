# P1.2 verifier, round 5: report

## Verdict: NOT READY

I found three defects in what the code does. Each is a crash or a wrong exit code on input the adapter should refuse or call misuse. None touches the real records or the real crates, and the checker refuses every crate involved, so there is no wrong acceptance. I found no defect in a gate, none in the cleanup beyond what limit 22 states, and none in how the generator derives a CHECKED value. Round 4's two fixes each stop one step short of their class; the fixes of rounds 1 to 3 held wherever I tried them.

Labels: MEASURED means I ran it, with the script named. READ means I read the code. BELIEVED means neither. All my scripts are in `<home>AppData\LocalLow\qro-sbx\p12-r5\s\`. The earlier verifiers' copies, with `p12-r4` changed to `p12-r5`, are in `s\r4\`. All code ran through sbx.sh and the runner through sbx-mid.sh. IBM job ids are masked.

The reproduction of all three defects is `<scratch>\verifier-P12-r5\check\repro_D1_D2.py`. Run it as `python repro_D1_D2.py &lt;a copy of the tree&gt; &lt;a new directory&gt;` through sbx.sh.

## Defects (all code: what the code does)

### D1. A lone surrogate in a record nested about 1,000 levels deep crashes the records' reader, and the adapter exits 3 where it must exit 1

- **Cause (READ).** `_unencodable` in `qro/p1_records.py` is round 4's fix. It is a recursive Python function that `parse` calls from inside its `except UnicodeEncodeError`.
  - The strict reader accepts nesting to about 2,996 levels (MEASURED: `depth_probe.py`, `depth_probe2.py`).
  - Python's recursion limit is 1,000, so `RecursionError` comes out where `RecordError` should.
- **Faults that show it (MEASURED).**
  - In process (`depth_surrogate.py`): `rec.parse(b'{"a":' + b'['*N + b'"\\ud800"' + b']'*N + b'}', 'x')`. N = 1 gives a `RecordError` naming `a[0]`. N = 1000 gives `RecursionError`, with arrays or objects.
  - As a process (`deep_surrogate_proc.py`): the twin as a slice, with `known-answer-line.json` carrying an extra member `x` nested N deep and holding `\ud800`.
    - N = 10, 500 and 980 give exit 1, `REFUSED metadata-generated ... G2` naming the field.
    - N = 1000, 1500 and 2900 give exit 3, `FAILED: the adapter itself failed, RecursionError: maximum recursion depth exceeded; this is not a verdict`.
    - The control, an encodable string at depth 1500, gives exit 0.
  - Atlas (`deep_atlas.py`): a real 2026-09-26 score file with the same member gives exit 1 at depth 10 and exit 3 at depth 1000.
  - My structural-poison fuzz (`s\r4\fz5.py`): 19 poisons in every small JSON file, digests resealed to a fixpoint, 874 trials on the twin and 475 on the Atlas crate.
    - The only crashes (180 and 108) are this one.
    - Every other poison was accepted or refused by a guard: a 3 MB string, 300,000 integers, 1e308, -0.0, 2^63-1, nesting of 1,500 or 2,900 with no surrogate, and a lone-surrogate key.
- **The checker refuses the same crate** (`s\r4\deep_checker.py`: `metadata-generated ... qro-p1-ibm failed on the records: RecursionError`). Only the adapter's exit code and message are wrong. This is round 4's D1, one condition further.
- **It contradicts (READ).** The `p1_records.py` docstring says "never a crash". The `p1_adapter.py` docstring says exit 3 "is never a verdict on the records". No test and no stated limit holds it.
- **Closure, the lead's choice.** In a copy (`...\p12-r5\fix1\`) I wrapped the `_unencodable` call in `except RecursionError`, with `place = "a field nested too deep to name"`. The repro then gives exit 1. An iterative `_unencodable`, or a depth bound in `parse`, would do too.

### D2. A degenerate UNC, extended-length or device `--out` is exit 3 where it must be exit 2, the out named

- **Cause (READ).** `_Made._first_under_out` converts the host's refusal only when `path.parent == self.out`.
  - pathlib joins the build's first entry onto `\\`, `//`, `\\server`, `\\server\`, `\\?\`, `\\.\`, `\\?\UNC\`, `\\?\UNC\server` and `\\wsl$` as a server and share. The entry's parent is then not the out.
  - So the host's OSError leaves as the adapter failing. 24 of about 45 prefixes behave so (`pathlib_family.py`).
- **Faults that show it (MEASURED).**
  - `outs_b.py`, under the guard: `\\`, `\\\`, `\\server`, `\\?\`, `\\?\UNC\` and `\\.\` give exit 3. The guard's refusal is an OSError, as the host's would be.
  - `outs_unc.py` and the repro, with the host's refusal simulated as WinError 53: those prefixes, `//`, `\\server\` and `\\?\UNC\server` give exit 3. The controls `\\server\share`, `\\server\share\x` and `\\?\UNC\server\share` give exit 2, "cannot be made (The network path was not found)". In the repro, `\\` also drew a real, unsimulated `OSError [WinError 64]` from the host.
- **It contradicts the page** (`docs/P1.md` 147-156) and the module docstring, which put an out the host cannot make, or cannot make the first entry under, at exit 2 with the out named. Round 2's D1 and round 3's N3 were this class. No test or limit holds it.
- **BELIEVED:** for `--out \\` or `//`, the build asks the network for a host named `2026-09-25` that the user never named.
- **Closure, the lead's choice.** In `fix1`, one guard in `check_out` (`if not out.exists() and out.parent == out: raise AdapterError(...)`) makes every prefix above exit 2. `C:x` and a relative new directory still build.

### D3. A `--moth` or `--records` that the host refuses to look at is exit 3, where an `--out` it refuses is exit 2

- **Fault (MEASURED, unsimulated).** `stat` of this PC's own admin share gives `WinError 65, Network access is denied`. In `denied_inputs.py`, as a process:
  - `--moth \\localhost\C$` gives exit 3 for the IBM build, the IBM slice and the Atlas build: `FAILED: the adapter itself failed, PermissionError: [WinError 65] Network access is denied`.
  - `--records \\localhost\C$` gives exit 3.
  - The control `--out \\localhost\C$\x` gives exit 2, "cannot be used (Network access is denied)".
  - `--records \\wsl$` gave exit 3 (WinError 64).
  - Every other odd value gave exit 2: a nonexistent path, a file, NUL, CON, a device, `\\`, `\\server`.
- **Cause (READ).** `moth.is_dir()` in `build` runs before any conversion, and so do the plan's `is_dir`, `is_file`, `iterdir` and `read_bytes`. pathlib ignores only not-found errors. Only `check_out` converts.
- **Simulated (`denied_inner.py`).** A checkout directory the host will not list, a vector it will not examine, a file it will not read, and the read's directory: all exit 3.
- **The docstring** says "2 is misuse, a checkout or an `--out` the adapter will not use". If the lead rules that an unreadable input is the adapter failing, the docstring and the page's exit-3 list need to say so. I report it as code, by the rule round 2 set for `--out`.

## Notes (they do not block)

**Prose, where the code is right**
1. The exit-3 list (`docs/P1.md` 161-164 and the docstring) is incomplete.
   - No `git` on the PATH is exit 3 (`nogit.py`, MEASURED).
   - A source record the host will not let the adapter read is exit 3 as well (BELIEVED).
2. Limit 22 names the swap of a directory the build made. It does not name a link put at the name of a directory the build has not yet made.
   - The build follows such a link, then removes what it wrote there if it fails. `h5_prejunction.py` (18 rows) and `a2_swaps.py` S1 (63 files written and removed) show this (MEASURED).
   - I judge it the same class as N1, so it is a gap in the sentence. The lead may rule otherwise.
3. `--moth` naming a directory with none of the records, with `--slice`, gives exit 1 `REFUSED spelling at ./ mentions: a list of one value or more`. It is a true refusal in a cryptic line.

**Test reach, where the code is right**
4. No test holds a deep nested record with an unencodable string, a degenerate UNC `--out`, or an unreadable `--moth` or `--records`. The three defects are those gaps. The branches of `_unencodable` for keys, lists and nested dicts are held.

**Other**
5. One of the six real Atlas job ids is a literal in `tests/p1/test_p1_records.py:289`, inside a copy of Quantum-Film's own commitments line.
   - The base's P1.1 `tests/p1/test_p1_graph.py:141` holds the same id (`find_atlas_id.py`, MEASURED).
   - It is a service identifier, not Moth's response data. The lead should decide whether it counts against "no byte of Moth's data in the tree".
6. P1.2's files hold two `atexit.register(shutil.rmtree, str(d), True)` calls: `controls/plants_p1.py:84` and `tests/p1crates/p1crates_support.py:41`. P1.1's `tests/p1/p1_builder.py:571` holds a third.
   - Each removes a directory its own process made with `tempfile.mkdtemp`, so each fits CLAUDE.md item 9 (READ).
   - A mutant of one is what the incident was, so the launcher must hold it.
7. The generator's `Crate` walk descends into a junction on Windows. The checker refuses a crate holding one first, with `file-link` (`crate_junction.py`, MEASURED). The adapter's plan refuses links. Only a link put in the out during a build (N1) reaches it.

## What held (MEASURED unless marked)

- **Freeze.**
  - `sha256sum -c` over the packet's tree gave 367 of 367, and `SHA256SUMS.txt` begins `484524e70ba442a0`. The twelve packet digests I checked equal the brief's. The tree equals the worktree file by file (`cmp`).
  - Against 37640f0 the packet adds 76 files and changes two: one bullet in `docs/README.md` and `GENERATORS` in `qro/register_p1.py`. No home path or address shape is in them.
  - The twin's 56 files (828,488 bytes) each equal `git cat-file -p 3a73823:&lt;path&gt;`, and none is an Atlas file.
- **Full runner** (my committed copy `c8038b9`, run `20261031-001425-7079-c8038b9`): 19 passed, 0 failed, 5 skipped by name.
  - p1 had 1,753 passed and p1-crates 41, the brief's figures.
  - The runner left the committed copy unchanged. moth-quantum's `.git/index` time (2026-10-15 20:43:39), its cleanliness and its HEAD were unchanged after the runner and every build.
- **Real crates** (the adapter as a process):
  - IBM: 1,073 files, 53,269,160 bytes, `8ec4dc39df52c0dc...`. Atlas: 31 files, 4,975,638 bytes, `f9c1a259786e3e9a...`.
  - Both are ACCEPTED by `python -m qro check` with those identities. The page's counts hold on them. The twin builds to one identity under four hash seeds.
  - Code of mine that imports no `qro` (`measure_ibm.py`, `measure_atlas.py`) gives 68 of 68 commitments equal in claim, line, record and echo, 12 digests in 6 classes, 57 plus 8 links, and 31 of 31 known answers msb-first with none mirrored. Atlas |z| is 2.15 / 172.96 / 346.28.
- **Round 4's fixes, apart from the three defects.**
  - 27 spellings were tried for each of the repository and the checkout (`outs_a.py`). 21 are refused as inside the repository and 22 as inside the checkout. The 22nd is an 8.3 alias. All give exit 2 with the out named.
    - The spellings include `\\?\`, `//?/`, `\\.\`, `\\?\Volume{guid}`, `\\?\GLOBALROOT\...`, `.` and `..` components (also under `\\?\`), `::$INDEX_ALLOCATION`, and another case.
  - Four network-share spellings are refused as unusable. This is limit 23's claim, true on this host.
  - Two spellings pass, and rightly: `\\?\&lt;dir&gt;.\x` names a literal sibling, and `&lt;dir&gt;:ads\x` cannot be made (`ads_probe.py`). Siblings with a similar name pass.
  - Eleven mutants of the out guard are killed. They ran without `-x` over the adapter's tests and the p1-crates adapter test. They built nothing in the mutant repository and attempted no write toward the real checkout, so the lead's ruling 3 holds.
  - Eleven mutants of round 4's additions (S1 to S6, C22, C23, B8a, B8b1, B8b2) are killed.
- **Round 3's fixes.**
  - Limit 21 on the real IBM crate (`real_snap_classes.py`, a hard-linked copy):
    - Exactly three classes of a Quantum-Film snapshot are ACCEPTED: the `date` of `gates/*/parameters/*`, of `general/*` and of `qubits/*/*`.
    - The other seventeen are refused `calibration-link`.
    - A prediction file plus one byte is ACCEPTED, and the real file was unchanged.
  - Outs of 32,768, 40,000 and 100,000 characters give exit 2.
  - Both new p1-crates tests passed under the guard that refuses a write to a hard-linked file, so no Python write reached the original through a link. The toolkit's one raw write follows an unlink (READ).
  - The junction test, forced to fail after its junction exists, leaves 0 links in the pytest base temp and in my directory.
- **Rounds 2 and 1.**
  - G9's requirement refuses nothing honest. 12 random honest slices of the real IBM records (`slices_random.py`) and the Atlas day slices (`atlas_slices.py`: 09-25 alone, 09-26 alone, both) were all built and ACCEPTED. Both days together equal the full Atlas crate.
  - Round 1's D1 and D2 are refused on the real Atlas records (`r1_checks5.py`: exit 1, G11).
  - The two unrequested changes hold: `GIT_OPTIONAL_LOCKS=0` (index time unchanged), and a foreign file at a write is exit 3 with the file left (F5).
- **Cleanup.**
  - The earlier verifiers' scripts, rerun on this tree:
    - `ca_inject` 80 of 80, `cb_foreign` 43 of 43, `cc_fail` 9 of 9.
    - `cd_process` 37 of 37, with exit codes 0, 1, 2 and 3 and never 120.
    - `h5_prejunction` 18 of 18, `a1_outs` 0 failed.
    - `h6_open_handle` leaves exactly the manifest and its five ancestors (C22's case). `h4_late_oserror` gives exit 3 with the world restored.
    - `a2_swaps` has one "fail", S2, the simulated check-to-unlink window that limit 22 states.
  - Of the earlier verifier's 25 adapter mutants, 24 are killed. C22, which survived in round 4, is now killed. C10 survives as before: it is equivalent unless a link is swapped between `mkdir` and `lstat`, which limit 22 states.
- **The generator copies no CHECKED value.**
  - By audit events (`t1_open.py`), it opened 72, 30 and 1,072 files of the twin, Atlas and IBM crate and never `ro-crate-metadata.json`. Its output is identical with the descriptor removed, garbage, or with every CHECKED term changed.
  - With every guard off, a sentinel returned by `commitment_of`, `claims`, `link_for`, the rule table's name or the file hash is the value of every `qro:commitment`, `qro:valuesDigest`, `stamp`, `newestValue`, `qro:calibrationLink`, `qro:decodeRule` and `sha256` (`t2_sentinels.py`).
  - 45 edits of the real IBM crate's metadata over all 15 CHECKED terms were all refused (`meta_sweep_real.py`), none accepted. For `qro:decodeRule` the first refusal is step 4's `commitment`, not step 5's.
  - All 21 of the earlier verifier's guard mutants are killed.

## What I did not do

- I did not run P2's real `qro/p2_measures.py` or the merge onto 83503b0. The seam was exercised only with the third verifier's stand-in, in a scratch copy of the tree.
- I did not test: a host with long paths off, a non-Windows host, a volume whose file numbers are 0, a host that opens dangling junctions, a host where `\\localhost\C$` opens, a `subst` drive, a FAT or exFAT volume, or a OneDrive folder.
- I did not sweep the 1,380-entity IBM crate leaf by leaf, repeat P1.2's 364 mutants, or run the quick budget alone. Its stages are a subset of the full run.
- I did not mutate `GIT_OPTIONAL_LOCKS`, since a survivor could rewrite moth-quantum's index. I checked the index time instead.
- I made no real network share. D2 rests on the guard's refusal, a simulated WinError 53 and one real WinError 64. D3 is unsimulated, but only on this PC's own admin share.

## Disclosures

- My first command, `mountvol 'C:\' /L`, was rewritten by Git Bash's path conversion into `mountvol C:\ L:\`. It failed with "The directory is not empty". `Get-Volume` shows no change.
- A draft command wrote `<home>AppData\Local\Temp\nonexistent` (14,898 bytes, the 291 repository-relative paths of 37640f0, no ids). I did not delete it, since my rule is to delete only inside my directory. The lead may remove it.
- A relative `--out ..\..\..\x` in my script `outs_b.py`, resolved from my world, built a crate (73 files, 4,300,007 bytes, the twin's records) at `<home>AppData\LocalLow\qro-sbx\x`, in the shared sandbox root and not in my directory. The guard allows the whole root. I did not delete it. The lead may remove it.
- I wrote `check\wt_changed.txt` with a shell redirect, not the Write tool.
- I ran a plain `git status` and `git log` in the P1 worktree. Its index time (2026-10-25 23:13:30) is unchanged.
- Some probes made name lookups and SMB attempts for made-up host names and for this PC's own admin share. All failed.
- The first full-runner command ran past ten minutes under load and the harness moved it to the background; it finished normally. One later command was stopped by the harness' safety check, which misread a loop as a removal. I did not retry it.
- I printed short prefixes of Atlas job ids to my console in three places, and no IBM job id unmasked as far as I know. Nothing with an id is in my notes or this report.
- My directory holds about 184 MB: copies, crates, logs, mutant copies, and `fix1` with the two small edits. I removed my large temporary worlds. The harness refused a separate report file, so this message is the report. My working notes are `...\verifier-P12-r5\check\notes.md` and `notes2.md` under the scratchpad path above.
