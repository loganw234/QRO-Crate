# P4.3 verifier, round 1: **READY**

I found no defect in the code, a gate, the shapes, the examples or the prose. Every claim I checked was either READ in the files or MEASURED in my sandbox. The notes below are below the bar.

My sandbox is `<home>AppData\LocalLow\qro-sbx\p43-r1\`. It holds `run1.log` and my probe scripts. Everything that runs Python ran through `sbx.sh`. The runner ran through `sbx-mid.sh`.

## What I checked

**Freeze.** MEASURED: `sha256sum -c` over `tree\` returns OK for all 513 files, and SHA256SUMS' own hash begins `569d2d4f57c33744`.

**Full runner.** MEASURED, on a git-committed copy (`f96fbe0`) with `QRO_MOTH_ROOT` and `QRO_SHACL_PYTHON` set:
- 23 stages passed, 1 skipped (p2-crates, by name), 0 failed.
- `p4` took 158 s and `p4-shacl` 189 s, with my mutation runs going alongside. The page says 143 s and 176 s beside other work, so this is consistent.

**Regenerated `profile/`.** MEASURED: `gen_profile.py --check` says every file is exactly what its definition renders. READ: the diff against main in `EXAMPLES.md`, `README.md` and `ro-crate-metadata.json` is the two matrix rows, the one sentence, and the matching size and hash changes.

**The twin as an example.**
- READ: `tests/p4/p4_twin.py` builds both twins only through `plants_p1.pristine_twin` and `pristine_twin_alone`, and `pristine_twin` builds into the system temp folder and removes it at exit.
- READ: a test asserts `profile/examples` holds only `fixture`. Both stages read the same `TWINS` list, and `test_p4shacl_twin.py` loads `p4_twin` through `quick_stage_module`.
- MEASURED: the page's numbers are right.
  - `p1-twin`: 74 files, 135 entities, 933 triples, all 63 terms carried, and every one of the 139 shapes has a node to read.
  - `p1-twin-alone`: 73 files, 107 entities, 746 triples, and 39 must and 2 should shapes have no node.
  - There are 131 must shapes in all.
- MEASURED: both twins conform in the evaluator and in the engine. The engine's triples equal the expansion's.

**My own faults planted in the twin.**
- I put a bad value on each carried term, one entity at a time and on all entities at once: 126 cases on `p1-twin` and 86 on `p1-twin-alone`.
- In none did a must shape fail where the checker's verdict is a name its claims lack.
- In none did the checker accept while every shape stayed silent.

**Soundness gate sweep.**
- MEASURED: the registry has 5 accepted rows, 4 of them crate plants (P1's twin plants, which the gate reaches) and 1, `shared-control`, with no plant.
- `test_every_accepted_crate_plant...` pins the walked count to the count of accepted rows that build as crates.
- I also checked all 20 refused rows by hand. Every must shape that fails on one claims the checker's refusal name. Three rows are custody logs rather than crates, and one is refused by the expansion itself.
- The builder is right: P2.2's refused plants are not walked by the gate. Nothing in P4 holds a refused registry plant to the claims, which is a note below.

**Note 1, the spy's lists.** MEASURED: I skipped each of the 34 names in turn in the spy's wrapping loop in `watch_below`. A test failed for all 34; none survived. The control, a spy without the name, sees nothing, or only the `os.stat`/`os.lstat` call beneath it for the six names the standard library makes through those two.

**Note 2, the import guard.**
- READ: each of the 21 `os` names and `subprocess`, with the alias, other-object, getattr and string spellings, is refused, and the plants pass the guard's test.
- READ: the page's claim that only `qro/p1_adapter.py` names a process call is true. `grep` over `qro/*.py` finds `subprocess` there alone. The tool calls only `checker.describe`, not `load()`.

**Note 3, `--help` exit 3.** READ: the sentence in `--help`, the docstring and the page all name a directory the host cannot list. The docstring's line 176 raises `Unlistable` for that case.

**Note 4, `--help` layout.**
- MEASURED: 17 of my 19 hand mutants of the layout in `gen_profile.py` died. They were widths 99, 101 and 60; indents of 4, 6, 1 and 4; "Exit codes:"; blank-joined exits; the default formatter; one and three spaces after the code; swapped order; a doubled and a missing trailing newline; usage suppressed; and the description with extra text in the epilog.
- The two survivors are equivalent: `break_on_hyphens=True` changes nothing because the text has no hyphen, and `RawTextHelpFormatter` only differs for the options' help, which the layout check doesn't assert.

**Junctions.** MEASURED, with `--basetemp` inside my directory and a scan for any junction or symlink:
- The passing run of `test_p4_tree`, `test_p4_crash` and `test_p4_twin` (283 tests) left none.
- A run with `remove_link` made a no-op, 24 tests failing, also left none.

**Files and bytes.**
- 12 files changed, all P4's: `docs/P4.md`, `profile/*`, `qro/p4_profile.py`, `tests/p4*` and `tools/gen_profile.py`. None is outside P4's.
- MEASURED: all are LF, ASCII, no BOM and end with a newline. `p4_helpers.py` has 20 non-ASCII bytes, the same count as at main.
- `privacy` and `privacy-controls` passed in the runner.

**Twin tests catching a stricter shape.** MEASURED: I made every word-set term's allowed list one word short, first dropping the last word and then the first. Both mutants were killed by the twin's plain-checker and expansion tests.

## Notes (below the bar)

1. **Gate reach, guard (test and prose).**
   - `imports_outside` does not see `os.__getattribute__('sy' + 'stem')`, `print.__self__.__import__(...)`, `type(os).__getattribute__(...)`, `sys._getframe().f_globals`, or `os.fork` and `os.forkpty` (not in the guard's process names; POSIX only).
   - The page admits the computed-`getattr` hole, and the test says "however it is reached".
   - I judge these deliberate evasions, not accidents, which is what the guard is for. The page could say the guard is a tripwire against accidental use.
2. **Gate reach, refused plants.**
   - Only `accepted` registry rows go through `accepted_control_problems`. No P4 gate holds the registry's refused crate plants to the claims. P2.2's two refused twin plants will not meet one either.
   - My ad hoc check over the current 20 refused rows found no problem. A standing refused-row sweep would close this.
3. **Merge-order.**
   - `test_the_twin_with_p2_carries_every_term_of_the_table` and the "every shape has a node" test read every term owned by P0, P1 or P2.
   - If P2.2 adds a P2 term that the twin doesn't carry, both tests, and the prose counts of 63, 131 and 8, will move.
   - That is the lead's merge entry; I did not test it.
4. **Registry.** `shared-control` (an accepted row) has no plant in `registry.plants()`, so no gate walks it. This predates P4.3.

## What I did not do

- I did not run P2.2's plants, because they are not in this packet.
- I did not time the twin's build in isolation. I have only the stage times above.
- I did not plant my own mutants in the engine stage (`p4shacl`). The twin file passed in the full runner and agrees with the evaluator on the one planted-wrong-measure case.
- I did not search for IBM job ids across the tree.
  - The privacy stages pass.
  - I printed no id.
- I did not run mutants against the runner's shell.
- I did not read the ledgers beyond the brief's summary. My judgment rests on the files, not on the builder's account.
