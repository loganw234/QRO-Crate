# P2.1 verifier, round 1: NOT READY

The code gave no wrong answer on anything I tried. The verdict rests on gates: the `p2` stage lets seven faults through that its own text claims to catch, and the test that holds the contract with P1's generator (T1) lets metadata-reading faults through too. In every case the shipped code refuses the fault when I plant it.

## Freeze and what I ran

- **Freeze (MEASURED).** `sha256sum -c frozen/SHA256SUMS.txt` is 323 of 323 OK, and its own hash begins `8b2dcb9925e0a31c`. The ledger and brief hashes match the packet. The worktree equals the frozen tree: the same 323 files, plus its `.git` link file.
- **Runner (MEASURED).** I made a commit of 37640f0's tree plus P2.1's files as the working change in `check\run`. I ran `QRO_MOTH_ROOT=<repos>/moth-quantum bash verify/run.sh` there. Result: 19 passed, 0 failed, 5 skipped by name (p4, p1-crates, p2-crates, profile, p4-shacl). It took 13:46:23Z to 13:50:48Z. The `p2` stage took 32 s, 467 passed. The run passed lint, docs, check-docs, privacy and privacy-controls.
- **Order (MEASURED).** The p2 tests also pass in reverse file order.
- **Scripts.** All my scripts are under `<scratch>\verifier-P21-r1\check\v\`. The mutation harness is in `...\check\v\mut\`.

## Defects

None is about what the code does. D1 to D5 are gates (the code is right, the tests would not notice); D6 is a claim made false by them.

**D1 (gate): the central invariant has a hole.** "Every carried gate list is held, whatever the claim" is untested when the Hold says `withheld` but some gate lists are carried.
- **Fault.** In `qro/p2_steps.py` `_compile`, after `g = carried[0]`, add `if hs[0].get("qro:exactHold") != "holds": continue`. All 467 tests still pass (MEASURED: my hand mutant H62, run against `tests/p2` in a workspace copy).
- **Crate it lets through.** The manifest names four gate lists. One is not carried, so the Hold honestly says `withheld`. A carried gate list is broken (a `cz` dropped from `law.gates.json`, every digest recomputed).
- **Shipped code (MEASURED, `withheld_broken.py`).** It refuses this crate: `compile-uncontrolled` at `bundle/law.gates.json`. A broken list that is carried but dropped from the Compile's `result` is refused too.
- **Why the tests miss it (READ).** In `test_p2_steps.py` the `withheld` crate carries no gate list, the `unexposed` crate names none, and no step-7 plant mixes carried and uncarried lists.

**D2 (gate): two checked terms have no plant.** The terms are `qro:upper` of a Measurement and `qro:twinValue` of a Contrast.
- **Faults.**
  - H8: `for term, i in (("qro:lower", 0), ("qro:upper", 1))` becomes lower only.
  - H6: the `qro:twinValue` comparison is dropped.
  - Both survive all 467 tests.
- **Shipped code (MEASURED, `gate_probes.py`).** It refuses an edited `qro:upper` and an edited `qro:twinValue`, both as `measure-class`.
- **Claims contradicted.** Design item 12 ("step-level plants, one per term"). The docstring of `test_p2_steps.py` ("every refusal of both steps, one plant each"). `docs/P2.md` ("Every claim here is held by a test or says it is not").

**D3 (gate): two counts have no plant.** The counts are a second `qro:Measuring` and a second `manifest.json` in a Compile's `object`.
- **Faults.**
  - H41: `len(measurings) != 1` becomes `&lt; 1`.
  - H33: `len(found) != 1` in `manifest_of` becomes `&lt; 1`.
  - Both survive.
- **Shipped code (MEASURED, `gate_probes.py`).** It refuses both (`measure-class` at `@graph`; `compile-uncontrolled` at the Compile).
- **Claim contradicted.** E2 (1) says "none or two is refused". Only none is tested (READ, `test_p2_steps.py:344`).

**D4 (gate): the sign of a coherence circuit's parity is not held.**
- **Fault.** H20: `abs(got - float(want))` becomes `abs(abs(got) - abs(float(want)))`. It survives.
- **Shipped code (MEASURED, `gate_probes.py`).** A transpiled `coherence-xx` circuit whose parity is -0.8 where the law says +0.8 is refused `compile-uncontrolled` at its gate list. The test named `...coherence_against_another_coherence...` does not cover the sign.

**D5 (gate): T1 does not hold what it states.** "contribute never reads the metadata file" is the point of T1, but three faults that read it survive:
- C1: the family taken from `#measuring` in the metadata file.
- C3: the Measuring's name taken from there.
- C2b: a Hold's word taken from the metadata's Hold of the same id.

T1's "another crate's" metadata is the real crate's. It has the same family (5) and name as the small crate and no Hold with the small crate's id, so the output is equal either way. Separately, no test calls `contribute(crate_dir, entities)` with two arguments, as P1.2's generator does. C7 (the default `source` changed to a digest no circuit has) survives. The shipped code reads no metadata (READ).

**D6 (prose): the sentence in `docs/P2.md` is false.** "Every claim here is held by a test or says it is not" is contradicted by D1 to D4. Restate it or add the plants.

Smaller gate gaps, same kind:
- Step 7 finds a logical circuit by digest anywhere in the crate, which the seam with P1.2's sheets relies on. Mutant H60 (find it only through the Compile's `object`) survives.
- Shipped code accepts the sheet shape (MEASURED).

## Everything else I tried held

### Classes and values (items 1, 3, 6)
- **Metadata edits (MEASURED, `mut_matrix.py`).** I edited every CHECKED value of the small crate's 30 P2 entities, and added every P2 term an entity could carry but does not. That is 1,083 edits.
  - Outcomes: 1,013 `measure-class`, 41 `spelling`, 18 `compile-uncontrolled`, 10 `step-unbuilt`, 1 accepted.
  - The accepted one re-points `qro:lawCircuit` to `bundle/law.qasm`, a circuit in the question's `object` that also lays the law. See Notes.
- **Values and classes (MEASURED, `values_check.py`, `classes_check.py`).**
  - All five law measures and both coherence measures equal my own formulas on the three devices' morning records. They also equal Quantum-Film's printed four-place figures.
  - 300 random count sets across all five law measures gave 0 mismatches, including the N=0 and unoccupied-site cases.
  - The 20 Contrasts equal my own computation from the law table.

### Law (item 4)
- **Table and circuit (MEASURED, `sim_real.py`).**
  - My own kernel and exact determinants give 4,368 layouts, 1,360 forbidden, minors summing to 1,048,576 = 16^5.
  - P2's table differs from mine in 0 layouts.
  - The law file is 78,482 bytes, SHA-256 `a242c4de…`.
  - My simulation of the source circuit lays it to 3.7e-17, and X0X1 = Y0Y1 = +0.374999999999994.
- **Law attacks on the real crate (MEASURED, `real_law.py`).**
  - A weight moved by 1/4096 is refused at `#question qro:lawCircuit`.
  - Doubling every weight and the denominator is accepted.
  - Editing the law file's `source` text is accepted.
  - Both accepted cases are covered by the stated limits and by step 9.

### Intervals (item 2)
- **Containment and tightness (MEASURED, `iv_check.py`).** I used mpmath at 60 digits, not P2's arithmetic, on 2,914 cases plus 300 fractional totals.
  - Cases covered p=0, p=1, n=1, n up to 2^63-1, and alpha, M and total varied.
  - 0 problems: every end is a grid point proven outside, and the next point inward is inside.
- **Pinned difference (MEASURED).**
  - I rebuilt the counts from the records: kingston 131,765 of 221,184, fez 147,047 of 270,336.
  - Kingston-less-fez is `[12330612205551/2^48, 16819644152847/2^48]`, so the pin is right.
  - The grid ends bracket the exact KL set ends by less than 2^-48 (kingston -1.6e-15 and +3.1e-15, fez -8.1e-16 and +2.1e-15).
- **Maps (MEASURED, `maps_check.py`).** The maps to each measure's units equal the crate's stored intervals.
- **Host independence (READ).** The path to the ends is integers and Fractions only, and `p2_interval` imports only `dataclasses` and `fractions`.

### Simulator and hold (item 3)
- **Random circuits (MEASURED, `sim_random.py`, `sim_random_big.py`).** V8 against my numpy simulator on 850 random gate lists and 850 random logical circuits, including pair expectations: worst difference 2.8e-15.
- **Real gate lists (MEASURED, `sim_real.py`).** All 12 distinct real gate lists of kingston, marrakesh and fez, and the 4 logical circuits: worst 1.0e-17. Worst (a) over every manifest entry of the three devices is 6.3e-17.
- **Fuzzing (MEASURED, `hold_fuzz.py`, `role_fuzz.py`).**
  - 495 mutants of carried gate lists (331 on the small crate, 164 on kingston's real lists), digests resealed.
  - 179 mutated logical circuits, re-transpiled, against their roles.
  - Compared with my own simulation: 0 wrong acceptances and 0 wrong refusals.
- **Tolerance (MEASURED, `tolerance.py`).** The hold flips where my own max difference is 1e-10, within 4e-18.
- **Phase plant (MEASURED).** An `rz(0.7)` before a measurement is accepted, as limit 1 says.
- **Plants named in `docs/P2.md` (MEASURED, `claims.py`).** All refused (a): 2.3e-3, 2.6e-3, 1.8e-3.
- **Reader and v0 files (MEASURED).**
  - P2's gate-list reader against Quantum-Film's own `isa.py`, loaded standalone from moth-quantum (`reader_vs_isa.py`): 6,000 corrupted lists. 5,000 both refuse, 997 both accept, 3 differ.
  - The 3 are `num_qubits = 2^70`, refused by P1.1's integer bound and accepted by `isa.py`. That is by design.
  - All 126 v0 QASM files, 124 gate lists and 31 manifests read (`qasm_all.py`, `manifests_all.py`).
- **Memo.** I found no way for one crate's verdict to depend on another's (READ: keys are digests, width and operations, the law digest; stored values are never mutated). The memo mutants C11 to C15 are killed.

### Entry rule, registration, hostile inputs, exit codes (items 5, 6, 8)
- **Entry rule (READ).** The reader refuses any key not in the vocabulary and any type not listed, so a P2 term or type cannot be spelled another way. `_enters` scans every entity of the graph for a step-6 or step-7 key, plus the types, as lists too. I found no way to carry a P2 term or type past it.
- **Registration and cost (MEASURED, `fixture_cost.py`, `fixture_poison.py`).** P0's fixture is accepted in process, and as a process (exit 0, `ACCEPTED 21fafec5…`) with all seven `qro.p2_*` modules poisoned. Only `qro.register_p2` is imported; it declares `STEPS` 6 and 7 and nothing else.
- **Hostile files (MEASURED, `hostile.py`).**
  - 186 hostile files in process: law, law circuit, manifest, gate list, logical circuit, resealed.
  - All are refused by the step's own name, except 3 manifests accepted (a CRLF one, one with a trailing line feed, and one with 120,000 entries that took 54 s).
  - Run as processes, 185 files gave exit 1 with the same lines. None gave exit 3 or 120.
- **Host failures (MEASURED, `host_fail.py`).** Inside the steps, PermissionError gives exit 2. OSError, MemoryError and KeyboardInterrupt give exit 3. RecursionError is a refusal. With stdout closed (`&gt;&amp;-`) the exit is 3, never 120.
- **Real-crate plants as processes (MEASURED, `real_broken.py`).** `compile-broken` (gate 303 `sx` to `x`) exits 1 `REFUSED compile-uncontrolled`, and `class-declared` exits 1 `REFUSED measure-class`.
- **Interpreter.** The withheld probes also ran on Python 3.13.5.

### Data and whose files (items 10, 13)
- **Data copies (MEASURED).** The ten copies equal `git show 3a73823:&lt;path&gt;` byte for byte. The README's paths, sizes (157,309 bytes in all), SHA-256s and MIT text are true. The two source-circuit paths are one blob.
- **Scans (MEASURED).** No key, home path, address or job id in P2's files. The only "logan" is the MIT copyright line.
- **File ownership (MEASURED, `diff -rq` against 37640f0).** P2.1 added only its own files, plus the one `docs/README.md` line. All are LF, and CRLF count is 0.

## Mutation (item 15)

All mutants were run against `tests/p2`; survivors against the whole stage.

- **Automatic, 902 mutants.**
  - Operators differ from P2.1's: boundary neighbour, negation, return-none, statement deletion, constants, arithmetic, index, test negation.
  - Count: 760 mutants cover every site of `p2_hold` (183), `p2_measures` (245) and `register_p2` (26), plus samples of `p2_law`, `p2_sim`, `p2_steps`, `p2_interval` and `p2_report`.
  - A further 142 mutants drop a boolean operand or a tuple element, at every such site of `p2_steps`, `p2_hold`, `p2_measures`, `p2_law`, `p2_sim` and `register_p2`.
  - About 70 live. All are equivalent, boundary (`&gt;` and `&gt;=` at exactly 1e-10) or unreachable, except these gaps:
    - the two in D2;
    - `parity` for a pair not starting at qubit 0 (`o &lt;&lt; a`);
    - `question_files`'s metadata skip below the root;
    - `measurements()` on a `none` value;
    - a Compile `result` holding non-gate-list files such as QPY (P2.2's twin covers it);
    - a QASM `cx` whose control is out of range.
- **Hand mutants, 81.**
  - They cover steps 6 and 7, the readers, the enclosure, memos and the contract.
  - Live: H6, H8, H20, H33, H41, H62, H60, C1, C2b, C3, C7, and H67 (equivalent: only three roles exist).
  - C6 and C8 are equivalent.

## Notes (code right; test reach or prose)

- **Dead code.** `Law.index` (`p2_law.py:107`) and `_MEASURE` (`p2_sim.py:192`) are never used.
- **Prose, limit 13.** "Cost grows with the distinct gate lists, a few tenths of a second each" is v0's figure.
  - One 20-qubit list of 218 gates took 10.8 s (MEASURED, `dos_cost.py`).
  - Extrapolating to the 100,000-gate cap gives minutes to hours (BELIEVED).
  - The memo's 64 entries are bounded by count, not bytes.
  - Restate the sentence at the merge.
- **No limit sentence for an orphan.** A File shaped like a gate list that no Compile's `object` or `result` lists and no manifest names is never examined (READ). Step 9 covers it, but `docs/P2.md` states no limit for it.
- **Logical circuit with a withheld list.** Its role (b) is not held; (b) piggybacks on a carried gate list. This is consistent with item 7.
- **`qro:lawCircuit` re-pointing.** Step 6 accepts a re-point to any circuit in the question's `object` that lays the law. The vocabulary's meaning allows it, and step 9 holds the choice.
- **Law file free text.** Its `stock` and `source` fields are unchecked beyond text spelling.
- **Entry-rule test.** `test_each_step_enters_on_its_own_terms...` is fine, but `register_p2`'s inner `isinstance(t, list)` is equivalent for string types.
- **Independence test.** It would not catch a `/` (true division) in `p2_interval`. The golden endpoints would.
- **E2 and the corrections of 12:01:15Z.** I judged each and found none that changes a verdict about an honest crate. `isa.py`'s read matches P2's reader as above.

## What I did not do

- **Lost interpreter.** Miniconda3's Python lost its `Lib` directory while I was running, so I could not run pytest or the runner again. I did not touch it, and a `conda.exe` process was running.
  - The fourth hand-mutant batch broke partway: H65, H66 and H68 to H74 (nine mutants) did not run and are not counted.
  - I did not re-run the runner afterwards; its one full pass is above.
  - The orphan gate-list case (Notes) is READ, not probed.
- **Missing by design.** I did not run P1.2's generator or twin, the controls, the `p2-crates` stage or Atlas crates. They are not in this packet.
- **Not measured.** I did not run the quick budget separately.
- **Masking slip.** I printed one IBM job id to my console once, in an unmasked key listing of a device-run record. It is in no file and not in this report.
- **Kept to the rules.** I used no key and no network, opened nothing under `~/.quantum-film`, edited nothing outside `check\`, and contacted no one.
