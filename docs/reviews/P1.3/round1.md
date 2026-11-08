**Verdict: READY.** I found no defect in the code, the gates or the prose. The notes below are small.

The full runner (through sbx-mid) had passed 12 stages when I wrote this. Those are lint, docs, check-docs, vocabulary, tool-tests, vocab-tests, format, custody, p1 (798 s), p2, p4 and p1-crates. The later stages (p2-crates, profile, p4-shacl, control-tests, controls-run, twin, controls, study, study-plants, privacy, privacy-controls, instruments) were still running. None of them touches P1.3's files. I did not wait for them.

## Freeze and scope

- **Freeze.** READ/MEASURED: `SHA256SUMS.txt` begins `1ff0681880c50d8c`, and every file of `tree\` matched its line.
- **Changed paths.** MEASURED: 8 paths differ from main at 118009a, the 8 the brief names. All are P1's, plus `docs/P2.md`.
- **docs/P2.md.** READ: only limit 15's last clause changed.
- **Line endings, ids and encoding.** MEASURED: all 8 files are LF only. The only non-ASCII bytes are U+2026 ellipses in `docs/P1.md`, which main already uses. No IBM job id was added to any changed line.
- **Privacy gate.** MEASURED: `tools/check_privacy.py` ran and listed only binary files it could not read, as before.

## 1. F1's closure (about what the code does)

I used a clone of moth-quantum at 3a73823, with a lying v2 `core.fsmonitor` hook that prints only a token. After priming, I checked that `git status --untracked-files=all` and `ls-files -v` said clean before each build. Each build ran the adapter as a process through sbx-mid.

- **IBM classes lost under the hook.** MEASURED: the build exits 2, names the file, and leaves no out directory. The classes were LICENSE, source circuit, prediction, snapshot, sheet and non-sheet manifest, README, qasm, qpy, gates.json, isa.qasm3, line, metrics, raw, submitting, verdict and pub record.
- **Atlas files lost under the hook.** MEASURED: exit 2 for LICENSE, vector, and each day's circuit, commitments, submit, status, result and score, for both days.
- **Files the plan does not walk.** MEASURED: a lost vector under an IBM build builds as before. That is correct, since the IBM plan does not walk the vector.
- **Honest checkout under the hook.** MEASURED: IBM builds with identity `88259c78…`.
- **Ways the builder did not try.**
  - A v1 hook (`core.fsmonitorHookVersion=1`, hook prints nothing) with a lost snapshot: exit 2 by the new hold.
  - Assume-unchanged, skip-worktree and a sparse checkout: exit 2 from the existing `ls-files -v` check.
  - A directory in place of LICENSE: exit 2.
  - An ignored untracked file beside the taken ones: exit 2.
  - A byte flipped with the stat kept, under the hook: exit 2.
  - LICENSE renamed to `license` with other bytes: exit 2. With the same bytes it builds the identical crate (Atlas `f657f60e…`), which is acceptable.
  - `GIT_DIR`, `GIT_INDEX_FILE` and `GIT_WORK_TREE` set in the environment: the honest checkout still builds, because the adapter strips `GIT_*`.
- **Not attempted.** Git's built-in daemon (`core.fsmonitor=true`): it spawns a detached process, which the host-trap rule forbids me to start. A file in place of a directory under the hook: my test left the status dirty, so I read the code instead. A lost file is refused by `hold_plan_to_tree` whatever replaced it, and the status check would catch the rest. An alternates file and `git replace`: BELIEVED fine, since `--no-replace-objects` is passed and HEAD's tree is content-addressed.
- **Real checkout.** MEASURED: the `p1-crates` stage passed (502 s). My own IBM and Atlas builds from the real clone were accepted as built, with the identities above.

## 2. N2

READ: the flipped-byte tests cover 10 IBM classes and 3 Atlas classes. Each asserts `git status` and `check_moth` clean first, then exit 2 and no out directory. I also flipped a byte by hand under the hook (stat kept), and it was refused. The hold is per file, not per class, so the unlisted classes (verdict, submitting, pub record, README, gates, isa) are covered by the same path. That is a gap in the tests' reach, not in the code.

## 3. N3

READ: the adapter docstring says "four things", numbered (1) to (4), and each matches the code: `git status`, `ls-files -v`, `hold_to_head`, `hold_plan_to_tree`.

## 4. The export

- **Conditions.** MEASURED: I normalised and diffed the AST of `_g2`, `_g3`, `_g4_g5`, `_g6`, `_g7` and `_g8` at 118009a against the exported functions. They differ only in whitespace and names, plus G8's `committed_path` parameter. G9 I read side by side: same conditions in the same order. `hold_refetch_result` takes `raw_path` and `committed_path`, and the generator passes `RECORDS_DIR + raw`, so the record is still held to the committed path.
- **One switch.** READ: the generator has no `_hold`, `_read` or `_gN`, and no `from qro.p1_guards import`. Every guard call is `p1_guards.hold` or `p1_guards.read_record`, looked up at call time. The functions in `p1_guards.py` call the module-global `hold`, so one patch reaches all of them.
- **Direct raises.** Two `raise GuardError` remain in the generator, as at 118009a: the G7 `LinkError` conversion and the `seam` raise in `call_p2`. Neither goes through `hold`. They are not record-claim guards, and the test counts them.
- **Imports.** MEASURED: `import qro.p1_guards` loads only `qro`, `canonical`, `checker`, `p1_commit`, `p1_decode`, `p1_forms`, `p1_graph`, `p1_records`, `reader`, `refusal`, `spelling` and `vocabulary`. No generator, P2 module or register module.
- **Pinning.** READ: the tests pin `EXPORTS`, every signature by string, the plain-namespace and four-key-dict calls, a spy that checks the generator reaches each guard through the module, and an AST check that the generator keeps no copy.
- **Identities.** MEASURED, main's code (`git archive` of 118009a) against the packet's, the adapter as a process on the clone:

| Crate | Files | Identity |
|---|---|---|
| IBM | 1,074 | `88259c78409248f7…`, both |
| Atlas | 32 | `f657f60e0e6a98e3…`, both |
| Twin with P2 | 74 | `231430759cfc…`, both |
| Twin alone | 73 | `4352ebc7ed3f…`, both |

  The IBM and Atlas file trees are byte-equal. Their metadata differs only in `datePublished` and `writtenAt`.

## 5. Round 8's note 1

READ: `docs/P1.md`'s seam section states "This stays a limit", gives the ruling, the measure, and the four tests it would have turned refused. `docs/P2.md` changed only limit 15's clause.

## 6. Unintended changes

READ: the only change to an existing test's strength is in `test_p1_generate.py`. It swaps the old counts (`len(holds) &gt; 60`, 4 raisers) for `&gt; 25` and `&gt; 30` over the two modules and 2 raisers each, and the test still checks the letters named. I saw no other moved guard, refusal, exit or page.

## 7. Junctions

MEASURED: I scanned pytest's temp folders modified in the last 3 hours and found no junction. This includes the runs of the p1 stage, which ran P1.3's tests. I did not touch the `garbage-*` folders.

## 8. The builder's slips

- READ/MEASURED: the files are LF, with no stray encoding.
- BELIEVED: the builder's slips as it described them, since I did not audit its sandbox.

## 9. Mutation

I ran 14 mutants of `p1_guards.py` (all against the packet copy, through sbx.sh): G2 `program`, G3 type check, `MAX_PUBS`, salt, G4 echo, G5 rows, G6 `finished` and `created`, G7 `running` and `gates_equal`, G8 `agree_at` and sizes, G9 max-one and carried-snapshot. `test_p1_exports.py` alone killed 10. The 4 it let survive (G3 type check, G8 `agree_at`, G8 sizes, G7 `gates_equal`) were each killed by the rest of `tests/p1`, which is also in the p1 stage.

## Notes (below the bar)

1. **Tests, not code.** `test_p1_exports.py` alone does not hold G3's `type(...) is type(want)` check, G7's `gates_equal` flag, or G8's `agree_at` and sizes. Other P1 tests do. If P5 reuses the exports tests alone as its pin, those four are not held there.
2. **Tests, not code.** N2 and the lost-file tests do not list every class of file by name.
3. **Prose.** `hold_plan_to_tree` says "before anything is written". The out directory is made first and then cleared on refusal, and I saw no leftover. Only files are meant, so this is a wording point.
4. **Prose.** The claim that one patch of `p1_guards.hold` switches off "G1 to G12" is true of every guard that goes through `hold`. It does not reach the two direct `raise GuardError` sites, which were the same at 118009a.
5. **For the lead, not a P1.3 fault.** The hooked tests and my own attacks run git's hook through sh, so sbx-mid is the only way to run them. This means the Python audit hook alone holds them.

## What I did not do

- Git's built-in `fsmonitor` daemon (above).
- The quick-budget runner.
- My own hand mutants of `p1_adapter`'s cleanup code. I ran only the adapter and attacks that delete test files in my clone, all through the launchers.
- Waiting for the last runner stages or for the lead's run id.
- An audit of the builder's sandbox for writes outside its directory.

Every file I ran or attacked is under `<home>AppData\LocalLow\qro-sbx\p13-r1\`. The attack scripts are `lost.py` and `atk2.py` there. The runner's output is `runner.out`.
