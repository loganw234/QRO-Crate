**Verdict: READY.**

I found no defect in what the code does, in a gate, or in a claim, and the frozen packet is intact. The probes were targeted, not exhaustive, and I did not run any mutation.

**The freeze.** READ and MEASURED. `SHA256SUMS.txt` itself hashes to `4a375105…`, and `sha256sum -c` over `tree\` found no mismatch. Against main's 411 files the packet changes 14 and adds 1, and every one is a file a ruling names.

**The runner** (MEASURED, through `sbx-mid.sh`, both `QRO_MOTH_ROOT` and `QRO_SHACL_PYTHON` set). I ran it on a `git init` copy (commit `cbb6df8`) and on main's history with `tree\` laid over it (commit `f67319a`, from `git clone --no-hardlinks`).
- Both runs passed 22 stages and skipped 2 by name, `p1-crates` and `p2-crates`.
- The unplanned `privacy` and `privacy-controls` stages passed over main's whole history, so the KNOWN entry and the redacted `round3.md` hold.
- `instruments` and `p4-shacl` ran in the history copy and passed.
- The unplanned `tool-tests` stage took 421 to 445 s on this shared machine.

**Scope 1, round 1's rulings**
1. **D1, the ruff walk** (MEASURED, my own script run on a copy with `d1.py`).
   - It caught a masking `ruff.toml` or `.ruff.toml` in 13 places: the root, each of the four lint directories, a deep subdirectory, `__pycache__`, a `.venv`, a `.git`, `node_modules` and `dist`. Names in other case (`RUFF.TOML`, `Ruff.Toml`, `.RUFF.toml`) were caught too, as was the lint directory `TESTS` (upper case).
   - It caught a `pyproject.toml` with `[tool.ruff.lint]` below the four directories, in any case.
   - It did not enter a junction below the four, and it did enter a lint directory that is itself a junction: with `controls` made a junction, a masking `ruff.toml` there was reported, and without one the tree was clean.
   - The files it did not flag are right to pass: `docs/`, `profile/` and `verify/` are not linted, a `pyproject.toml` with no `[tool.ruff]` table is not a configuration, and `ruff.toml.bak` is not a name ruff reads.
   - I did not re-run ruff 0.11.9 to confirm the junction behaviour. I tested only the gate's side of the builder's correction. That is BELIEVED consistent with the builder's measurement.
2. **D2, the drive designator** (MEASURED, `check` and `custody` as processes, 32 arguments each, via `d2.py`).
   - `C:.`, `c:.`, `C:..`, `C:.\x`, `C:..\w`, `C:/.`, `C:./x` and `C:\` each gave exit 1 `REFUSED file-missing`, the verdict of what they name, the same as `.`, `..` and `.\x`.
   - `C:crate.`, `C:x `, `C:...`, `C:.\crate.`, `1:.` and `CC:.` gave exit 2 naming the argument. `Z:.` and `x:` gave exit 2 "no such crate directory".
   - `D:.` gave the verdict of drive D's current directory.
   - The `\\?\` and `\\.\` forms gave the verdict of the entry named. No argument gave exit 3 or the verdict of another entry.
   - `custody` gave exit 2 for every argument, as none names a file.
3. **D3, FORMAT.md item 16** (READ). Each answer's line-start claim matches `__main__.py`: the argument as written for an empty name, a wrong-kind path, an unusable name and an unlistable crate, and the place the host refused for a path reached through the argument.
4. **Notes 1 to 4.** The registry stage passed with the stream limit, item 9, the docstring and the guard-order tests present. I did not re-measure `icacls` or the AC folder.
5. **The builder's correction to ruling 1** is consistent with what I measured on the gate's side (see D1).

**Scope 2.**
- `gen_vocabulary.py` under `python -OO` gave help and error text, and `--check` ran, with no crash (MEASURED).
- The three WSL alternatives and their plants are in `check_privacy.py`, and `privacy-controls` passed (READ and MEASURED).
- The junction guard (`assert_no_link_below`) removes only links found below the test's own `tmp_path`, with `os.rmdir`, which on a junction removes the link and not its target. It deletes nothing it did not find as a link, so I judge it safe (READ).

**Defects.** None.

**Notes (below the bar)**
- Prose and test reach, code right: no gate reads a file-level `# ruff: noqa` comment, which would drop a whole source file from the lint. `grep` finds no such handling or mention. It is outside "ruff's configuration" as ruled, so it is a possible later parcel.
- The ruff walk is wider than ruff in default-excluded directories such as `.venv`. This is the lead's decision, and it fails closed.
- The `docs` and `tool-tests` stages are slow beside other work: 118 to 121 s and 421 to 445 s here. That is not a fault.

**What I did not do**
- No mutation runs.
- No test of Python 3.13 or 3.14.
- No new privacy-gate planting beyond the stage's own controls.
- No `icacls` re-measure.
- No read of the builder's or round 1's sandbox directories.
- No check of the CLAUDE.md edit by the lead beyond the packet text.

Files are in `<home>AppData\LocalLow\qro-sbx\p09-r2\`: `d1.py`, `d2.py`, `run-hist.log` and `run-gi.log`. Nothing is left running, and I made no junctions that were left behind. I wrote no check directory under SCRATCH, so this report is the only record.
