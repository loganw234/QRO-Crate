# 2026-10-14: IBM's own copies of Quantum-Film's 65 jobs of 2026-10-05, read

**What this is.** A read of IBM's own copies of Quantum-Film's 65 jobs of
2026-10-05, made with the owner's key, for study QRO-0's question 4. Logan
approved it on 2026-10-14: "go ahead with the key use".
- It submitted nothing and used no QPU time.
- The key and the instance's CRN stayed in files outside every
  repository. Neither was printed or written.
- The account was reached only through Quantum-Film's
  `quantum_film.ibm.account` and `keyleak`, from moth-quantum at
  3a73823.

**The tool and its environment.**
- The tool was `docs/studies/qro0/ibm_refetch_v0.py`, SHA-256
  `aeed00ca…`.
- It ran under the qf-ibm virtualenv: python 3.12.9, qiskit 2.5.2,
  qiskit-ibm-runtime 0.50.0, numpy 2.5.3.

## The runs, in order, failures included

1. **A trial on one job**, `db1nn11b694s73dsidjg`, written to the
   session's scratch directory, not here.
   - **The first attempt failed** before writing anything:
     `TypeError: Object of type QuantumCircuit is not JSON serializable`.
     The client's `job_get` had already decoded the parameters, and the
     tool decoded them a second time. The second decode was removed.
   - **The second attempt** wrote three files. Every hold was equal.
2. **All 65 jobs.**
   - **The first attempt never started.** The shell could not open its
     log, because `records/2026-10-14/` did not exist yet.
   - **The second attempt** ran from 15:40:22Z to 15:42:40Z by the local
     clock, and wrote `ibm-refetch/`:
     - 65 job records;
     - 7 distinct property snapshots;
     - `MANIFEST.json` (SHA-256 `1761adbb…`), which holds every other
       file's SHA-256 and size.
   - Its full output is `ibm-refetch.log`.
3. **A scan of everything written** for credential and e-mail patterns
   found none. `user_id` appears only as the name of a key the tool
   omitted.

## What it established

Measured by `docs/studies/qro0/calibration_at_execution_v0.py` and its
output.

**The anchors.** For all 65 jobs:
- IBM's created time equals the job line's `submitted_at`;
- each of the 68 PUBs' `qf_commitment`, inside IBM's own copy of the
  submitted circuit, equals the line's commitment;
- each circuit IBM holds has the frozen bundle's gate list, layout
  included;
- the options and the shots IBM holds equal the manifest's.

**The calibrations.** These are the snapshots nearest before each job's
first shot, by IBM's history, keyed by storage time:

| device | execution-time snapshot | values differing from the freeze snapshot | on the chain |
|---|---|---|---|
| kingston | 09:02:46Z (the 3 morning jobs) | 0 of 6,211 | — |
| kingston | 11:28:27Z (10 jobs) | 342 | readout and T1/T2 unchanged; CZ errors moved by a mean of +0.0003, at most 0.0024 |
| kingston | 12:21:18Z (6 jobs) | 680 | the same chain changes |
| marrakesh | 09:51:18Z (3) and 11:21:28Z (20) | 2 of 6,230 | none |
| fez | 10:08:31Z (3) and 11:44:47Z (20) | 0 of 6,203 | none |

**What this changes:**
- **The stamps are not the content.**
  - Between the freeze and the morning runs, the values did not move on
    any device. kingston's sheets later ran under changed CZ errors.
  - Each snapshot re-dates 1,900 to 3,300 of its values without changing
    them.
  - Each holds measurement dates 2 to 4 minutes after its own stamp.
- **One job crossed a snapshot boundary.** kingston's known-answer job
  `db1pgmjid5ic73erg1u0` was running at 12:30:20.6Z under the 11:28:27Z
  snapshot. Its first shot, at 12:30:44.6Z, falls under the 12:21:18Z
  snapshot.
- **`properties()` is a timestamp match, not a link.**
  qiskit-ibm-runtime 0.50.0's `RuntimeJobV2.properties()` keys on the
  job's `running` time (base_runtime_job.py:199-214). It returns the
  nearest snapshot before it, a timestamp match the client makes.
- **The morning predictions were not stale.** They were built from the
  values in force. The predicted runs' shortfall against their devices
  is not a stale-calibration effect, as far as IBM's reported values go.
- **Quantum-Film's results document overstates one point.**
  docs/HARDWARE-RESULTS.md:194 says "kingston recalibrated between its
  bundle's freeze (06:57:43Z) and its run". For the morning run, the
  values IBM reports did not change between the two. The stamp did.
  This is recorded here, and not edited there: that file is Quantum-Film's
  own record.

## What it did not establish

- **That a snapshot was in force.** History is keyed by storage time, so
  "nearest before" is a necessary condition, not a proof.
- **The raw result bytes.** This read fetched each job's document,
  parameters and metrics, not its results. Section "The results,
  re-fetched", below, closes that.
- **Anything about the Atlas runs.** Their provider never held a
  commitment.

## The results, re-fetched (a second read, the same day)

**Its standing.** Logan's word, 2026-10-14, after the first read: "You
are clear to use the IBM key however needed, only requiring permission
for real QPU work". This read is read-only and used no QPU time.

**The tool and its runs.**
- `docs/studies/qro0/ibm_results_refetch_v0.py`, SHA-256 `f1187989…`,
  on the same guarded path and the same virtualenv.
- **A trial on one job**, `db1nn11b694s73dsidjg`, wrote to the session's
  scratch directory. It agreed at the bytes: 60,033 bytes from IBM, and
  60,033 committed.
- **The run on all 65 jobs** wrote `ibm-results-refetch/`: 65 job records
  and `MANIFEST.json`, SHA-256 `59ac54a2…`. Its output is
  `ibm-results-refetch.log`.
- **The scan for credential and e-mail patterns** found none.

**What it established.** For all 65 jobs, the text IBM returns today for
`GET /jobs/{id}/results`, as UTF-8, is byte for byte the raw result
Quantum-Film committed on 2026-10-05.
- Every one agreed at the first tier, the bytes. So the JSON and
  shot-by-shot comparisons never ran.
- The raw bytes are therefore bound to the provider's own copy, as of
  this read.
- A raw result re-sealed with a moved shot, the stated limit
  `shot-moved-resealed` of study QRO-0, would now be caught by the same
  re-fetch. That binding is a stage that needs the owner's key, and it
  lasts only while IBM keeps the jobs.

**What it did not establish.** That the results IBM holds are what the
device measured. The provider's copy is the furthest point a re-fetch
can reach.

## Corrections, 2026-10-14, after study QRO-0's draft 3 re-check

The verifier of draft 3 (on Sonnet) found that this record states four
things too loosely. The lines above stand as written; these replace
them. Each figure is from `docs/studies/qro0/calibration_at_execution_v0.py`,
as revised for draft 4, which refuses to run unless this read's
`MANIFEST.json` and every file it lists hash as recorded.

- **"The values did not move on any device"** is false in letter.
  - Between the morning freeze and the morning runs, the reported values
    did not move on kingston or fez.
  - On marrakesh, 2 of 6,230 moved. Both are the `rzz` `gate_error` of
    the coupler (65, 66), listed in both qubit orders, which rose from
    0.0029 to 1. That coupler is not on its chain, qubits 0 to 15.
- **"Each snapshot re-dates 1,900 to 3,300 of its values without changing
  them"** is false for kingston's later snapshots.
  - Against the morning freeze, kingston's 11:28:27Z and 12:21:18Z
    re-date 2,640 and 3,316 values, and change 342 and 680.
  - The five snapshots that served kingston's morning jobs and every
    marrakesh and fez job re-date 1,922 to 1,984 values each, and change
    at most 2.
- **"Nearest before each job's first shot, by IBM's history, keyed by
  storage time"** describes the query, not the result. The table's
  snapshots are what IBM's history returned for a query at each first
  shot.
  - That the history is keyed by storage time is an inference.
  - What was measured: 12:21:18Z was not returned for a query 9.0 minutes
    after its stamp, and was returned 9.4 minutes after it.
  - So 8 kingston jobs whose first shots fell between 12:26:17 and
    12:29:52Z were linked to 11:28:27Z, although 12:21:18Z was already
    stamped and fully measured. Which of the two was in force for them
    is not known.
- **"The freeze snapshot"** means the morning bundle's freeze throughout.
  The sheet bundles were frozen against other snapshots:

  | device | sheet bundles | frozen against | against the snapshot in force |
  |---|---|---|---|
  | kingston | 8 | 11:05:15Z | no record carries it, so the change since is not measured |
  | marrakesh | 10 | 09:51:18Z | 0 of 6,230 values differ |
  | fez | 10 | 10:08:31Z | 0 of 6,203 values differ |

  "kingston's sheets later ran under changed CZ errors" holds against the
  morning freeze.

2026-10-14, after study QRO-0's draft 4 re-check: the coupler (65, 66),
its rise from 0.0029 to 1, and its being off marrakesh's chain are
printed by `calibration_at_execution_v0.py` from draft 5 on. In draft 4's
version of that instrument they were read from the snapshot files and the
gate lists, not printed.

## The dry-run probe, 2026-10-14 (read-only)

Logan, 2026-10-14, verbatim: "Dry runs are safe and clear to run anytime,
only the real QPU runs are a hold point".

- **The tool** is `docs/studies/qro0/ibm_dryrun_v0.py`, on the same guarded
  path as the reads above.
  - In qiskit-ibm-runtime 0.50.0, a dry run renames the backend to its mock
    counterpart before submitting ("ibm_kingston" to "mock_kingston"). It
    refuses if the account has no such backend
    (qiskit_runtime_service.py:1102-1111).
  - The tool submits only when the account lists that mock backend.
- **The probe** (`--probe`) submits nothing. It wrote
  `ibm-dryrun-probe/probe.json`, SHA-256 `8a721e8d…`. Its output is
  `ibm-dryrun-probe.log`.

**What it established:**
- **The account's plan** is `open`, pricing `free`.
- **Its backends** are ibm_fez, ibm_kingston and ibm_marrakesh, and no mock
  backend. So IBM's dry run is not available to this account today: the
  runtime would refuse it. No dry run was submitted.
- **Its usage, as IBM reports it:**
  - 353 of 600 seconds and 5.448 of 10 resource units consumed;
  - 247 seconds remaining.
- **The window rolls.** IBM gave the usage period as 2026-09-16T19:37:20Z
  to 2026-10-14T19:37:20Z, ending at the query. So v0's charges of
  2026-10-05 roll off on 2026-11-02.
- **What was not kept.** The usage's `instance_id` and `plan_id` are named
  in the record, not kept.
- **A scan** for credential and address patterns found none.

## The dry-run probe, second run, 2026-10-14 (read-only)

Study QRO-0's draft 7 re-check found that the first probe tested only the
account's listing. The runtime's dry run also looks a mock backend up by
name, with one configuration request: a GET
(qiskit_runtime_service.py:1004-1029).

- **The tool** is `docs/studies/qro0/ibm_dryrun_v0.py`, with `--probe`
  extended to make that lookup for each device.
  - It passes the instance, so the runtime has no instance to guess and
    log.
  - It keeps only the exception's class.
  - It refuses to write a URL-quoted CRN as well as a plain one.
- **The record** is `ibm-dryrun-probe-2/probe.json`, SHA-256 `4d5510e0…`.
  - The log, `ibm-dryrun-probe-2.log`, keeps the runtime's three warnings.
    Their IBM request trace ids are replaced by `<redacted: IBM request
    trace id>`.
  - Nothing was submitted.

**What it established:**
- the same plan, the same three backends, and no mock backend listed;
- by name, IBM answered 404, "device not found", for mock_kingston,
  mock_marrakesh and mock_fez, and the runtime raised
  QiskitBackendNotFoundError for each;
- so IBM's dry run is unavailable to this account, both ways.

**A correction to the first probe's section above.** "Its usage, as IBM
reports it" lists 247 seconds remaining.
- IBM reports the limit, 600, and the consumption, 353.
- qiskit-ibm-runtime computes the 247 from them on the client
  (qiskit_runtime_service.py:1316-1330).
- IBM's 353 equals the sum of v0's 65 charges.

## Notes on the probe records, 2026-10-14 (after study QRO-0's draft 8 re-check)

- **The second probe's log.** When its trace ids were redacted, its line
  ends were also converted from CRLF to LF. Nothing else changed: the
  re-check reproduced the kept log from the original byte for byte.
- **"The runtime would refuse it",** in the first probe's section, is
  settled by the second probe's section: no mock backend resolves by
  name either.
- **A scratch trial.** Before the first probe, one trial of `--probe`
  wrote a probe file in the session's scratch directory, at 12:36 local
  time. It is not a record, and it submitted nothing.
- **The tool's versions.** The first probe ran `ibm_dryrun_v0.py` at
  SHA-256 `84a7d2d6…`, and the second at `ef6aafa3…`. Later edits to the
  tool rename a variable and correct its docstring, and run no probe.
- **The first probe's gate.** Its section says the tool "submits only when
  the account lists that mock backend". That describes the first version,
  `84a7d2d6…`. From the second probe on, the tool gates submission on the
  by-name lookup instead.

## Provider content, 2026-10-14 (after the providers' terms were read)

[NOTICE.md](../../NOTICE.md), at the repository's root, says which of these
files' contents are IBM's, which are this repository's, and what was left
out. In short:
- **The seven `properties-*.json`** are IBM's snapshots, as IBM's history
  returned them. No licence is claimed over them.
- **Each job record** in ibm-refetch/ holds selected fields IBM reported,
  beside comparisons and calibration pointers computed here. The first
  section's "65 job records" are these: they are not IBM's whole job
  documents, and they hold no circuit.
- **ibm-results-refetch/** holds digests and sizes of IBM's result text,
  and no result content.
- **The probes** hold the account's plan and usage, as IBM reported them,
  without its instance or plan ids.
