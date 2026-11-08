**Verdict: NOT READY.** One gate lets a masking ruff configuration through, the command line wrongly refuses some valid names, and one new sentence in FORMAT.md is false. Everything else I tried held.

## What I ran
- **Freeze (MEASURED):**
  - `SHA256SUMS.txt` begins `9b64b3d7`, and `sha256sum -c` over `tree\` passes all 412 files.
  - The 15 changed files in the P0.9 worktree hash equal to `tree\`. A `diff -rq` against main shows exactly those 15.
- **Full runner, two copies (MEASURED, sbx-mid.sh, `QRO_MOTH_ROOT` and `QRO_SHACL_PYTHON` set):**
  - A `git init` copy: run `20261031-061638-13945-0b91c28`, 22 passed, 0 failed, 2 skipped by name (p1-crates, p2-crates).
  - A `--no-hardlinks` clone of the real history, with `tree\` laid over and committed: run `20261031-061657-14065-2313134`, same tally.
  - On the history copy the privacy stage read 412 files, 13 messages and 170 earlier versions, with four known findings and 43 of 43 controls caught.
  - The tests total 4,997, and the seven P0 stages gain 339 over main.
- **Probes:** about 30 probe scripts in `p09-r1\probe\` and 30 mutants of my own (22 killed, 8 survived). Nothing is left behind: a scan of my directory finds 0 links.

## Defects

**D1 (gate). The docs stage's ruff pin passes a masking ruff configuration that ruff reads.**
- **Where:** `ruff_configuration_problems` in `tests/docs/test_stage_registry.py` (lines 908-944) uses `named_below`. It compares names exactly, and it skips any directory that holds `pyvenv.cfg` or `conda-meta/history`, plus `.git` and `__pycache__`.
- **Ruff does neither (MEASURED, ruff 0.11.9, full copies of the tree, real tests):**
  - A root `RUFF.TOML` with `[lint] ignore = ["F401"]` and an unused import in `qro/`: `ruff check qro controls tools tests` prints "All checks passed!", and `test_ruffs_own_configuration_is_what_the_lint_assumes` passes.
  - `tests/zz/pyvenv.cfg` beside `tests/zz/ruff.toml`: the same result.
  - Ruff does lint a directory that holds a `pyvenv.cfg` (it reports F401 when no `ruff.toml` masks it). So the carve-out "one in a virtual environment is not reported" rests on a premise that is false for ruff.
  - `Ruff.toml`, `.Ruff.toml`, a capitalised `Pyproject.toml`, `conda-meta/history` beside a config, and a config in `__pycache__` behave the same.
- **Tests and prose:**
  - `test_a_ruff_file_in_a_virtual_environment_is_not_reported` pins the hole.
  - My case-folding mutant survives the module's tests.
  - CLAUDE.md line 41 says "anywhere on disk in the tree", which the gate does not hold.
  - pytest's own pin next to it is case-blind on Windows, so the two are inconsistent.
- **Fine in this area:**
  - The `[tool.ruff]` pin itself is exact.
  - Dot-directories, `tests/` and nested pyprojects with a table are caught.
  - A gitignored `ruff.toml` is applied by ruff, so the lead's choice to walk the disk is right.

**D2 (code). `reads_as_another` refuses a drive-relative `.` or `..`.**
- **Where:** `qro/__main__.py` lines 84-95 exempt a component that is exactly `.` or `..`. A drive designator is part of the first component, so `C:.`, `C:..`, `C:.\x` and `C:..\x` end in a dot and are refused as "a name the host reads as another".
- **Fault (MEASURED, as processes, cwd a crate, main against the tree):**
  - `check C:.`, `C:..` and `C:..\crate`: main gave the crate's own verdict; the tree exits 2.
  - `custody C:.\good.log` and `C:..\crate\good.log`: main ACCEPTED; the tree exits 2.
  - `C:crate` is right, and `C:crate.` is rightly refused.
- **Tests:** the READ_AS table has no row for these. A mutant that strips the drive designator first passes all 176 non-bash tests of `test_cli.py`.
- **Prose:** FORMAT.md item 16 says "any component, but `.` and `..`", so the code also differs from its own page.

**D3 (prose). FORMAT.md line 214 is false for one of the answers it covers.**
- **Where:** the new sentence reads "Each answer is exit 2, never exit 3, and its line begins with the argument as the user wrote it".
- **Fault:** the list above it includes a path the user may not read or list. That answer's line begins with the file name of the host's error.
- **Evidence (MEASURED, in process, `os.listdir` told to refuse):** argument `./crate` gives `crate\inner: cannot be read here, Permission denied; ...`, not a line beginning `./crate`.
- **Fix:** restate it for the answers P0.9 adds.

## Notes
1. **Stream limit (prose, below the bar).**
   - FORMAT.md line 402 says "on a listed file". It is true and pinned.
   - It is narrower than the behaviour (MEASURED): a stream on the metadata file, on a directory and on the crate directory is also accepted with the same identity.
   - METHOD section 6 says to state a limit by the behaviour it concedes.
2. **CLAUDE.md item 9 (MEASURED, `icacls` read only).** Every named folder is Low, and the profile, AppData, Local, Temp, Roaming, source, repos, QRO-Crate, moth-quantum and the worktree are unlabelled. By the builder's own walk the counts match: 22 `AC` folders, 1 `LocalCache\LocalLow`, 16 others. A 23rd package's `AC` is a reparse point the walk skips. I only sampled "nowhere else in the system".
3. **Gate reach, below the key threat model.** The WSL gaps the docstring states are exact. It is not the only gap: the JSON-escaped mirror spelling `//wsl$\\Ubuntu\\home\\x` is found by no alternative. None of 5,184 spellings changed against main, no ReDoS, and the 1,280 realistic ones are all found. The KNOWN blob `b0b507f` is `83503b0:docs/reviews/P0.7/round3.md`. With the entry removed, the blob id changed, or the alternative wrong, the gate fails on it. Shipped, it passes.
4. **Test reach, code right.**
   - `unlistable` is pinned only under `check --fixtures`. My mutant restricting it to `--fixtures` survives, and real use has no `--fixtures`.
   - A lone space or dot-space component is not in the rule's table.
   - The junction guard works only because `no_link_left_behind` sorts before `registered`. Renamed to sort later, tests that plant `os.scandir` error at teardown.
   - `named_below` uses `os.walk`, which descends into junctions on this host. Ruff does not follow them.
5. **Files no ruling names.** The `docs` stage description in `verify/run.sh` changed by one clause. It falls within ruling 2's subject, and I do not count it as a defect, but the lead's decisions do not address it. The CLAUDE.md ruff bullet, item 10 and item 11 were kept by the lead.
6. **UNC edge.** A UNC server written with a trailing dot (`\\localhost.\C$\...`) is refused as "reads as another". That is misuse, not a wrong verdict.

## The rest of the scope held
- **Ruling 1, `-OO` (MEASURED):** 14 tool invocations give identical exit codes and output with and without `-OO`, except that `--help` prints no description. `--write` produces the committed bytes. `__doc__` is read only at `gen_vocabulary.py` line 153 and `gen_profile.py` line 293, both guarded. There is no `assert` or `__debug__` in `qro/`, `controls/`, `tools/` or `verify/`.
- **Ruling 3, WSL:** all nine of P0.7's third verifier's spellings are now found, each by exactly one alternative; main found five.
- **Ruling 4, command line:**
  - 40 argument shapes (every character the host refuses, plus control characters, DEL, non-breaking space, CJK, emoji and shell characters) give exit 2 naming the argument, for both commands.
  - Trailing space and dot tails, middle components, `.`, `..`, `\\?\`, `\\.\`, `NUL` and `CON` are as claimed.
  - Four folders the host denies listing give exit 2 "cannot be read here"; main gave exit 1 `file-missing`.
  - I found no exit 3. D2 is the only wrong refusal.
- **Rulings 8-10:**
  - The junction guard removes only links inside `tmp_path`, and a removed link's target is untouched. A left dangling link is named and not removed; I removed it by hand.
  - MH, MC, MD and C1 are each killed by a test that holds what its name says.
  - The constants test never skips, and the entries named with a trailing dot or space are refused `file-link` as documented.
- **The lead's three edits and decisions:** the three edits are exactly as described. The KNOWN entry and the guard removing links are right. The name rule is right apart from D2. Reading the disk is right, but the exemptions are too wide (D1).

## What I did not do
- Python 3.13 or 3.14 runs, and any other platform.
- The quick budget on its own, since the full run contains it. p1-crates and p2-crates were skipped by name.
- The builder's 80 mutants; I ran 30 of my own.
- A scan of the whole profile with `icacls`; I read the named folders and `Packages` only.
- I attempted `qro check` on four folders the host denies (`Application Data`, `Cookies`, `System Volume Information`, `Windows\CSC`). Each answered "Access is denied" and no content was read.
- I ran `check_instruments.py` once, read only, against moth-quantum. There was no IBM or Atlas contact and no key read. No IBM job id was printed.
- I could not write the report to the check directory: the harness refused the Write call (it says subagents return findings as text), so this message is the report. The probes and copies are under `<home>AppData\LocalLow\qro-sbx\p09-r1\` (`probe\`, `holeA`, `holeB`, `hist`, `gi`).
