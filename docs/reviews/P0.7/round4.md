# P0.7's fourth verifier, round 4

**Verdict: READY**, on the relaxed bar (CLAUDE.md item 6). I found no defect in what the code does, in the gates, or in the tests and registry that hold them. Everything below is a note. The runner passed in three copies and the gate found no key in about 300 random repository states. Each claim is marked READ, MEASURED or BELIEVED. My scripts are in `&lt;home&gt;\AppData\LocalLow\qro-sbx\p07-r4\mine\` and my notes in `&lt;scratch&gt;\verifier-P07-r4\check\notes.md`.

**One thing for you to clean up.** One of my background commands wrote a 187-byte file, `oracle-b.out`, directly in the owner's repos folder, the parent of QRO-Crate. Its redirect was evaluated in the shell's own directory, because the `cd` sat inside the first half of two backgrounded groups. It holds only the launcher's "REFUSED, the working directory is outside the sandbox" and "exit=125", and nothing ran. I left it, since the brief says to delete only inside my directory. Please delete it by that path.

## Defects
None in code, gates or tests.

## What I checked

**Freeze.**
- MEASURED (`sha256sum`): `SHA256SUMS.txt` begins `f38a4841b95b3f3d`. All 300 files in my copy of tree\ match, with no extras.
- MEASURED (read-only `git ls-files -s`): the packet equals the real staged index, blob for blob.
- Against cbdb6a3: 4 files added, 22 modified, none deleted.

**Runner.** MEASURED, through `sbx-mid.sh` with `QRO_MOTH_ROOT` set, in three copies. Each gave 18 passed, 6 skipped by name, exit 0, and 2,948 tests: docs 190, tool-tests 204, vocab 12, format 1,318, custody 23, p1 1,169, control-tests 32.

| Copy | Run id | Gate read |
|---|---|---|
| `git init` copy | `20261026-145604-53324-d7fc828` | 300 files, 1 message |
| `git clone --no-hardlinks` of the real history, remote removed, packet committed over cbdb6a3 | `20261026-145605-53367-72a0b58` | 300 files, 9 messages, 140 earlier versions, the 3 known findings |
| `git init` copy at a path containing a space | `20261026-155059-11245-622d39c` | stages passed |

- `privacy-controls` caught 40 of 40.
- 0 of 618 object files in the clone have a second name.
- At low integrity (`sbx.sh`), the seven pytest directories gave 2,925 passed and 23 failed. The 23 are the bash tests (exit `0xC0000142`): 2 in `test_cli.py` and 21 in `test_stage_registry.py`. That is exactly item 9's two files, and the new cut tests pass there.

**Round 3's fixes.**
- MEASURED (`hm_t.py` on a copy, after `check_ids.py` and an unmutated baseline of the 8 targets, 20 passed): the lead's four mutants are all killed by their targets. They are T1 (count by escaped length), T2 (cut only REFUSED lines), T2 (cut only descriptor 1) and T3.
- The cut tests and 13 gate tests also pass with a pytest base temp whose path holds a space.
- T3, the no-.git test, holds wherever the temp directory lies. With the guard's mutant, the test fails under the default temp folder and under `--basetemp` inside a git work tree (`CalledProcessError`, `git ls-files -t -c -d` exit 128). Unmutated, it passes inside the work tree (`mk_t3.py`).

**Round 2's fixes.**
- The lead's five mutants are 5 of 5 killed by target.
- The three runner mutants are 3 of 3 killed at mid integrity (`m_runner3.py`).
- Item 8's sentence holds (`streams_probe.py`): under both launchers with `&gt;&amp;-`, `sys.stdout` is None and a child started with `stdin=DEVNULL` starts, with no WinError 6.

**Item 9's hook paragraph.**
- MEASURED (`guard_probe.py`, `guard_probe2.py`): I ran the guard with a narrower root, `QRO_SBX_ROOT` set to a subdirectory of mine, so "outside" was still inside my own directory. 43 of 51 rows were refused under each launcher: open modes, `os.open` flags including `O_TEMPORARY`, remove, rmdir, rmtree, rename, replace, move, the copy family including `copy2`, chmod, utime, truncate, mkdir, writes through a junction, sqlite3, `_winapi.CreateFile` and `CopyFile2`.
- The one mismatch was my own expectation: `os.link(outside, inside)` is allowed, but any write through the second name is then refused.
- The by-design rows (ctypes, `os.system`, subprocess) went through, as item 9 says.
- MEASURED (sha256): the guard installed in `agent-venv`, `agent-mid` and `agent-test` is the third version.

**Differentials, old tree (cbdb6a3) against the packet.**
- `canonical.write` gives identical bytes for four P1 test models.
- `python -m controls.run` output is identical, 31 lines.
- Reader, deep paths: peak memory at 10,000 segments is 2.9 MiB against 192.4 MiB. 50,000 segments read in 0.114 s on this loaded host, and 100,000 in 0.227 s.
- Reader, wide trees: 100,000 files and 125,000 balanced files use the same memory as before, with no time regression.

**The id rule's cost.**
- A scan of every string literal in qro/, controls/, tests/ and tools/ finds only term keys, never an @id, whose scheme is a term. "No parcel writes one" therefore holds for the tree.
- Schemes refused include `data`, `geo`, `about`, `maps`, `query`, `tool`, `isbn` and `issn`.
- Schemes accepted include `http`, `https`, `urn`, `doi`, `orcid`, `ror`, `ark`, `hdl`, `tel`, `git`, `s3`, `mailto`, `ibm`, `ibmq`, `qiskit` and `crn`.

**Gate.**
- Random repository states against real commits (`gate_oracle.py` to `gate_oracle4.py`). In a copy of each state I ran a plain commit, `commit -a`, and `add -A` plus commit, then looked for the key with `git log -S`.
  - 300 states, 0 misses. In 38 clean states the controls also returned 0.
  - The same oracle sees the pause's bug: 1 miss on a gate whose pass-over asks git alone.
- 17 states disagreed with the oracle in the safe direction. Fourteen were a tracked path replaced by a directory, reported `unreadable: PermissionError`. Three were a key on disk that no commit would take: an untracked file outside the sparse patterns, and skip-worktree or assume-unchanged files. Neither is a defect (see note 5).
- Real paths of 419 characters (LongPathsEnabled is 1; git run with `core.longpaths` set): clean passes the run and the controls, and a key is found on disk and as a staged version.
- A real cone sparse checkout of the history clone, 263 of 300 files off disk: `privacy` passes (37 files, 263 staged versions, 140 history versions, 3 known) and `--control` catches 40 of 40.
- The gate's patterns find nothing in the pending commit message.

**Mutation of my own.** Eight mutants: 7 killed by their targets, and 1 equivalent because no two-character non-prefix term exists. They covered a lost `geo`, the cut's stream, a MemoryError caught as a refusal, the path tree's kinds, the descriptor, the writer's net and step 9's net.

**Prose.**
- The five entries' mutant counts add up to 52 (17+12+12+2+5+4).
- Their test counts sum correctly (2,923, 2,940, 2,941, 2,946, 2,948).
- The reviews README's escape and redaction counts match the files.
- All 12 notes in `NOTES.md` are taken.
- FORMAT.md items 16 and 22 and the docstrings agree with the code. I checked the cut, the MemoryError arms, the id rule and the `geo` mapping against the pinned context.

## Notes (none blocks)

1. **Prose and guard: item 9's "nowhere else in the profile" is false.**
   - READ (`icacls`): besides `AppData\LocalLow`, these profile folders carry `Mandatory Label\Low Mandatory Level:(OI)(CI)(NW)`, and the user's DACL gives full control or modify. A program Python starts, which the hook does not see, can therefore write and delete there.
     - `&lt;home&gt;\AppData\Local\Temp\Low` (the owner's Temp, empty)
     - `&lt;home&gt;\Favorites` (3 entries)
     - six `&lt;home&gt;\AppData\Local\Packages\*\AC` folders
     - `&lt;home&gt;\AppData\Local\Publishers\8wekyb3d8bbwe\MicrosoftStore`
   - The scan was bounded to 2,126 directories and 100 s, so the list is not exhaustive. I demonstrated no write.
   - `&lt;home&gt;\source`, `repos`, QRO-Crate and moth-quantum carry no low label.
   - Suggested wording: name those folders, or say "LocalLow and the few folders Windows itself labels low".
2. **Prose: "no parcel writes one" reaches further than was measured.** The VALIDATION entry and the pending commit message both say it. I measured P1.1 (1,169 tests) and the tree; the entry itself measured P1.1 and P4, but P2 is not in the tree and was measured by no one.
3. **Guard (outside the tree).**
   - MEASURED, print only: a child `python -S` (or `-I -S`) loads no sitecustomize, so it has no hook. Under `sbx-mid.sh` nothing else holds it. Item 9 says the hook does not see programs Python starts, so this is consistent, but the guarded `python` is not inherited by such a child.
   - MEASURED: `tempfile.mkdtemp(dir=&lt;a place the hook refuses&gt;)` retries the refused mkdir 10,000 times on Windows. My watchdog fired at 90 s, so a refusal looks like a hang.
4. **Tools (outside the tree), `hm_t.py`.**
   - READ: its only check on `WORK` is that it lies under the shared `qro-sbx` root. It then runs `rmtree` on it, so a mistaken `WORK` naming another agent's directory would be removed.
   - Under `sbx.sh` it reports any survivor as "KILLED (pytest, not by its target)", because the 23 bash tests always fail there. My equivalent mutant showed this.
5. **Known, older than P0.7, held by a test, not counted.** A tracked file replaced by a directory is reported `unreadable: PermissionError` even when nothing is unread. It showed in 14 of 300 random states, always fail-closed. The gate also reads a key on disk in a file git will not commit (skip-worktree or assume-unchanged, or untracked outside the sparse patterns).
6. **Cut, as round 1 noted:** a long `where` leaves no room for the detail. The test pins this.
7. **Pending commit message** still holds the `VERDICT_PARAGRAPH` placeholder.

## What I did not do
- P4's stages (not in the tree), any other platform, a real symbolic link, a case where git sees a file and Python cannot, and any Python but 3.12.15.
- Anything under pythonw.exe, detached, or in a new console (forbidden).
- IANA's registry: not fetched. I did not run rdflib or the SHACL environment: item 22 is unchanged since round 3 except item 16's wording, which I read against the code.
- The lead's earlier 43 mutants, P0.5's 300,000-id sweep, and round 2's and 3's writer matrices and 126-state gate matrix. My oracle is a random sample and thinner than that matrix in the rare classes.
- No write outside my directory to demonstrate note 1.

## Deviations
- The stray file above.
- Read-only PowerShell outside the launchers: `icacls` on about 2,100 profile directories and 13 named folders (only the low-labelled ones printed; I skipped the credential and `.atlas` directories and the repos folder), and a listing of my own processes.
- I stopped one hung probe of mine by PID (python, command line `guard_probe.py`).
- I set `QRO_SBX_ROOT` to a subdirectory of mine for the guard probe, using `sbx_run.py`'s documented override. All writes stayed in my directory.
- I removed one copied file in my directory by its literal path.
- I wrote nothing to `/tmp` and printed no IBM job id. Key-shaped strings were built at run time from the gate's own plant.
- The harness refused a draft report file, so the report is this message. `notes.md` exists in the check directory.
