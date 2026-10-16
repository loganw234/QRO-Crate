# Study QRO-0: the quantum difference between two runs, and the crate that isolates it

STATUS: the plan of record. **Draft 12, 2026-10-14.** Logan approved it
that day, and it was amended the same day for its re-check's notes
(section 17). Nothing here is built yet, and no format is fixed beyond
the decisions Logan has made (below).

**How it got here:**
- **Draft 1** (SHA-256 `06dd0522…`) got "not READY" from its verifier,
  which ran on the session's default model: findings D1 to D14.
- **Draft 2** (`3164fbc3…`) got "not READY" from its re-check, on Sonnet:
  findings R1 to R12.
- **Draft 3** (`94e8116b…`) answered them. It recorded Logan's
  decisions, folded in two reads of IBM's own records made with Logan's
  key (section 4.5), and rewrote the comparison around the standard
  Logan adopted (section 8). Its re-check, on Sonnet, found V1 to V8.
- No verifier has called for a redesign.
- **Draft 4** (`c43b0f51…`) answered them. Its re-check, on Sonnet, found
  every answer right and five one-line slips, W1 to W5.
- **Draft 5** (`c964b81e…`) answered them. It also sized the next round
  as a free-tier unit anyone can repeat, as Logan asked (section 9.1).
  Its re-check, on Sonnet, found X1 to X8: six text slips and two missing
  limits.
- **Draft 6** (`b6c1515c…`) answered them. It recorded Logan's hold on any
  real run until a functional prototype exists, and made that prototype
  the first round's target (section 13). Its re-check, on Sonnet, found Y1
  to Y4, all text slips.
- **Draft 7** (`46156b38…`) answered them. It added three things from
  Logan: dry runs cleared, federated custody (section 9.2), and the Moth
  pilot (question 19). Its re-check, on Sonnet, found Z1 to Z12: claims
  past their evidence, and text slips.
- **Draft 8** (`0b0d4fb4…`) answered them, recorded Logan's two licences
  and a second read-only probe. Its re-check, on Sonnet, found AA1 to AA3:
  two in the custody log and one count.
- **Draft 9** (`c13af7e5…`) answered them. Its re-check, on Sonnet, found
  AB1: two stale draft numbers, the fourth time that slip recurred.
- **Draft 10** (`8e5936b7…`) answered it, and added a gate,
  `check_study.py`. Its re-check, on Sonnet, found AC1 to AC3: two text
  slips, and the study claiming more for the gate than it checked.
- **Draft 11** (`f74f112a…`) answered them, and strengthened the gate.
  Its re-check, on Sonnet, found AD1 and AD2: the study still claimed
  more for the gate than it checked, in section 17 and for output hashes.
- **Draft 12** answers AD1, AD2 and the re-check's notes 1 to 9 (section
  17). Note 10 was Logan's to decide.
  - The gate now checks most of what it left unchecked, and says it
    checks nothing else.
  - A new instrument, `check_study_plants.py`, tests the gate.
- **Then** a re-check of draft 12's changes, on Sonnet, found it READY,
  with no defect and notes N1 to N9.
- **Logan approved draft 12** (`f8a983e9…`) as the plan of record on
  2026-10-14 (section 14). A dated amendment took the notes the same
  day (section 17).

**Logan's decisions and aims, verbatim, all 2026-10-14:**
- "Both layers, go ahead with the key use, adopt it": question 1 is (c),
  question 4 is approved, question 11 is adopted;
- "You are clear to use the IBM key however needed, only requiring
  permission for real QPU work";
- "Going forward utilize Sonnet as the verifier agent model choice,
  they've proven capable at the task, as well as parcels when the
  direction is clear enough";
- "Ideally we can size a run that can be repeated by anyone on a free
  tier to give adequate data, allowing anyone to contribute more runs of
  the same thing for no cost. I'll still run multiple batches myself when
  the free quota refreshes" (section 9.1);
- "Hold off on a real run until we have a functional prototype "crate",
  rather than running bits and pieces. That also helps keep our runs as
  similar to a strangers as possible" (question 9, section 13);
- "Dry runs are safe and clear to run anytime, only the real QPU runs are
  a hold point" (section 13);
- "CC BY 4.0 for the data licence works": question 18 is decided;
- "MIT for the code license works too, unless it would be simpler to keep
  both CC BY 4.0". The lead advised against CC BY 4.0 for code;
- "MIT confirmed, docs CC BY 4.0, go ahead with git init": the code is
  MIT, the documents are CC BY 4.0, and the repository is initialized
  (question 10);
- "One key future addition is that this system should ideally be designed
  for federated custodianship, the end goal being QRO crates are able to
  be archived and audited by multiple groups independently." The rest of
  that message is quoted whole in section 9.2;
- "You have standing permission to download small things when it makes
  it easier for you, papers, packages, etc.";
- asked "Approve draft 12 of QRO-0 as the plan of record, with every
  recommendation as written?", Logan chose the lead's option "Approve as
  recommended". Draft 12 is the plan of record, every recommendation is
  adopted, and question 13 and question 16's agreement tolerances stay
  open (section 14);
- "A link is fine rather than full legal text as well": `LICENSE-docs.md`
  grants CC BY 4.0 by a link to it (question 10).

**Statement kinds.** Every statement below is one of four, and says
which:
- **READ**: from a file at the commit given below, or from a page named
  in section 3;
- **MEASURED**: run for this study, by an instrument named where its
  figure is used;
- **PROPOSED**: this study's design, a proposal for Logan unless a
  decision above covers it;
- **BELIEVED**: reasoning not tested here.

**What was read, and who read it.** Repositories are named by their
GitHub names; `moth-quantum` is the folder holding Quantum-Film.
- **The commits:**
  - Quantum-Film at 3a73823 (2026-10-05);
  - cft-fp256 at f22e8d2 (2026-10-13);
  - HonestFramework at 65447fd (2026-09-12);
  - ParcelRound at f42242e (2026-10-03), its `origin/main`, read with
    `git show`. The local checkout is 37 commits behind.
- **The readers:**
  - The lead read the methods, Quantum-Film's documents, and the cited
    parts of cft-fp256's.
  - Three read-only agents surveyed the trees first, each reporting file
    and line. That is ParcelRound's "Survey the tree before the plan,
    read-only" (METHOD.md section 1).
  - The two verifiers re-read the cited ranges and recounted the records.
  - Where a figure comes from an agent's report, the lead re-measured it,
    or the text says whose it is.
- **The instruments** are in docs/studies/qro0/. The five that analyse
  Quantum-Film's records refuse to run unless moth-quantum is a clean
  checkout of 3a73823. The three IBM tools read the provider.
  `check_study.py` checks this study's own text, and
  `check_study_plants.py` tests that check (section 15).

## Contents

0. The short answers
1. Why, in the owner's words
2. What "the quantum difference" means
3. The survey: RO-Crate, its run profiles, and quantum provenance
4. What Quantum-Film carries, and what IBM's own records add
5. Rules for deciding a field
6. The causes of a difference
7. The measures: signal or integrity, decided by the authority
8. The comparison, under the adopted standard
9. The crate
10. The authority and the checker
11. The controls
12. What v0 does not do
13. A first round, if this is approved
14. Questions for Logan, with recommendations
15. Sources
16. Kourousias et al., "Sufficient quantum provenance"
17. Send-backs: what each draft changed for its verifier

---

## 0. The short answers

1. **A cft certificate covers a run that is a function of its inputs. A
   QRO-Crate covers one that is not.** It aims to make everything around
   the shots a function of the record. What it cannot make so, such as
   the calibration in force or the provider's settings, it names, with
   the evidence it has and an absence word for the rest. Between two
   runs, a difference is attributed only to what is named as differing.
   A factor named `unknown` could differ too, and the comparison says
   so. PROPOSED. (Sections 1 and 6.)
2. **A comparison states, measure by measure, two layered statements**
   (question 1, decided). Each is a certified verdict under the adopted
   standard: **differ**, **agree** or **unresolved**, at a declared
   tolerance and confidence. Every cause that stopped a statement is
   named. PROPOSED. (Section 8.)
   - **Isolated from the pipeline:** the question and what was submitted,
     the producing commit included, are EQUAL; the compile is EQUAL or
     logically equivalent; bit order is held. The runs then differ beyond
     each run's own drift.
   - **Isolated as quantum:** in addition, readout's effect is bounded
     below that margin, and the measure is a signal against its named
     classical twin.
3. **"Quantum" is decided by the exact law against named classical
   twins**, on expected values that do not depend on the shot count. The
   classes are:
   - **integrity:** the five-crystal share, the one-site occupations and
     the crystals per shot;
   - **distribution:** the forbidden share, TVD, XEB, the pair
     occupations and the NN correlation. These separate the law from
     random placement, the uniform twin;
   - **coherence:** ⟨X0X1⟩ and ⟨Y0Y1⟩. These also separate it from the
     dephased twin.

   PROPOSED. The law's and the uniform twin's values are READ; the
   dephased twin's are BELIEVED until computed. (Section 7.)
4. **What a comparison cannot see:**
   - what its runs share;
   - a factor that differs together with the device. In v0 that is the
     time block: each device's jobs ran in their own blocks, in the
     morning and in the sheets;
   - a fabricated run with fresh identities, which only the provider's
     copy can expose.

   READ and MEASURED. (Sections 6, 8 and 12.)
5. **IBM's own records anchor v0 and bind its raw bytes** (MEASURED,
   2026-10-14, read-only):
   - for all 65 jobs, IBM's created times equal the job lines;
   - all 68 commitments sit inside IBM's copies of the submitted
     circuits;
   - every circuit IBM holds has the held gate list;
   - all 65 results are byte-identical to the committed raw files.

   The calibrations IBM's history returns for the morning jobs, and for
   all of marrakesh's and fez's, hold the morning freezes' values, but
   for 2 on marrakesh.
   - None of 6,211 differs on kingston, and none of 6,203 on fez.
   - On marrakesh, 2 of 6,230 differ, both on a coupler its chain does
     not use.
   - The stamps moved, and so did 1,922 to 1,984 per-value dates.
   - Kingston's sheets (12:21 to 12:37Z) ran under 342 or 680 values
     changed since its morning freeze.

   So a calibration is identified by its values, not its stamp. (Section
   4.5.)
6. **On v0's data, under the adopted standard, kingston against fez.**
   This is exploratory, at ε = 0: this study chose the comparison after
   reading the data (`selector-late`).
   - their day means **differ** in the five-crystal share, by at least
     0.0438, and in the forbidden share, by at least 0.0040;
   - XEB and both coherences are **unresolved**;
   - no measure's difference clears the drift within each run, and the
     producing commit is `unknown`, so nothing is isolated from the
     pipeline, let alone as quantum;
   - had one cleared it, the difference would still be the
     device's-and-its-time's: each device's jobs ran in their own blocks
     of time.

   That is v0's answer to the owner's question, stated as v0's limit, not
   as a failure of the format. MEASURED. (Section 6.1.)
7. **The next run is a free-tier unit that anyone can repeat** (Logan's
   aim; section 9.1).
   - Three devices run three interleaved passes of a control job and a
     film job: 18 jobs, 180 to 216 QPU-seconds. They are the three that
     ran v0 on 2026-10-05, and the only three Logan's account lists on
     2026-10-14. That every free account reaches the same is BELIEVED.
   - IBM's Open Plan gives 10 QPU-minutes per rolling 28 days, so anyone
     on it can run two units a window.
   - One unit is projected to certify the largest differences:
     kingston's five-crystal share against both other devices, and,
     thinly, its ⟨X0X1⟩ against fez, beyond readout.
   - Pooled units are projected to certify most of the other differences
     of means within 1 to 11 units, and some beyond readout within 27.
     The verdicts stay valid as units arrive, within the scope section
     9.1 states.
   - XEB, the forbidden share between marrakesh and fez, and kingston
     against marrakesh on coherence beyond readout stay unresolved at
     100 units.
   - Drift between units decides whether the devices differ in every
     unit. It is unmeasured until the first units run.
   - No real unit runs before a working prototype crate exists, by
     Logan's word, and that is decided. Logan's units then run through the
     same kit as a stranger's. That is this study's reading of Logan's
     reason, "as similar to a strangers as possible" (section 13).

   PROPOSED, except the hold, which is decided. The figures are
   projections from v0's data, and the costs are estimates. (Questions 9,
   15 and 16; sections 9.1, 13 and 16.5.)
8. **The shape:** RO-Crate 1.3 with Process Run Crate 0.6, and a QRO
   profile carrying cft-fp256's certificate rules:
   - one spelling for each value;
   - a strict reader that refuses by name;
   - every field CHECKED, READ, ANCHORED or REPORTED;
   - absence written as a word;
   - the metadata generated from the records, never written by hand.

   PROPOSED. (Sections 5 and 9.)
9. **Built for federated custody** (Logan's aim; section 9.2).
   - Crates are meant to be archived and audited by many groups
     independently: Moth first, as a pilot; then perhaps ASU.
   - A crate's digest is its identity, and any checker re-derives it.
   - Audits are records beside a crate, never edits to it. Each
     custodian keeps its own custody log, and a disagreement between
     auditors is a finding, not a vote.
   - A provider's records anchor other producers' runs on its platform,
     for an auditor who fetches them from it. Its own runs stay REPORTED
     until signatures exist.
   - Moth's coin toss engine is one qubit, a Hadamard, and counts
     (READ, from its published description). Its crates could audit its
     bias and drift, run by run, but not its correlations between shots.
     Its outcomes alone could not show that its randomness is quantum.

   PROPOSED. (Section 9.2; questions 17 to 19.)

## 1. Why, in the owner's words

Logan, 2026-10-14, verbatim: "I'd like to create a 'subspec' of sorts
that allows quantum compute runs to isolate the actual quantum difference
between runs reliably. For reference there, see how 'quantum-film' was
handled, as that will likely be the v0 spec/data source".

Three documents already say where this starts. All three are READ.
- **Quantum-Film's determinism contract** (moth-quantum,
  docs/DETERMINISM.md:10-12): "The Born rule is not made deterministic.
  Nothing can do that. A roll laid by a device is unique. What this
  project makes deterministic is everything around the shot".
- **cft-fp256's certificate study** (cft-fp256, docs/studies/CERT-V2.md,
  section 15): "No PROV-O, SLSA or RO-Crate serialization is part of
  version 2. Sections 2 and 3 map the fields, and that mapping is how an
  exporter would write one."
- **Quantum-Film's roadmap** carries from its first round "A bundle
  format: one job made 1,995 files" (moth-quantum, docs/ROADMAP.md:86).

So a cft certificate covers a run that is a function of its inputs, and
an audit proves it by re-running segments (cft-fp256,
docs/CERTIFICATES.md:56-94). **A QRO-Crate covers a run that is not.** It
aims to make everything around the shots a function of the record. What
it cannot make so, it names, with its evidence and an absence word. A
comparison then attributes a difference only to what is named as
differing. PROPOSED.

## 2. What "the quantum difference" means

**Decided by Logan, 2026-10-14: reading (c), both layers.** The three
readings were:
- **(a) The device against the pipeline.** The part of a difference due
  to the device, not to the logical circuit, compile, submission,
  decode, analysis or sampling.
- **(b) The quantum against the classical.** The part no classical model
  gives, measured against a named classical twin. Quantum-Film already
  does this for one run: "a value of either sign away from 0, beyond its
  error, is coherence that no reshuffling of layouts gives" (moth-quantum,
  docs/PREREGISTRATION.md:250-252, READ).
- **(c) Both, layered.** (a) first, then (b) within the device's part.

Section 8 states (c) as two statements:
- **isolated from the pipeline**, which is (a);
- **isolated as quantum**, which is (b) within (a).

The device's part includes its readout and, for v0, the time block it
ran in (section 6). So a readout fault can make a difference "isolated
from the pipeline". It cannot make one "isolated as quantum", because the
second statement needs readout's effect bounded (section 8). v0's
controls do not bound it.

## 3. The survey: RO-Crate, its run profiles, and quantum provenance

Read on 2026-10-14. **Page** means the page itself was read, through a
fetch tool or downloaded. **Search** means only the text a search result
returned. Pages read through the fetch tool are that tool's extraction,
not byte-verified, except where downloaded.

**RO-Crate 1.3.0** (its release on GitHub, ResearchObject/ro-crate;
page):
- published 2026-06-22, with status "Recommendation";
- permalink https://w3id.org/ro/crate/1.3, and context
  https://w3id.org/ro/crate/1.3/context;
- it moves schema.org to v30.0. Among the terms that adds are
  `Certification` and `Credential`; 1.3 itself uses none of the new
  terms.

**Profiles** (the specification's profiles page; page):
- a crate declares a profile in `conformsTo` on the root data entity;
- each declared profile has a contextual entity typed `Profile`;
- "The profile URI MUST resolve to a human-readable profile description".
  The 1.2 and 1.3 pages say the same (draft 2's re-check);
- a Profile Crate lists its resources with `hasResource` and a
  `ResourceDescriptor` each, with roles including `specification`,
  `constraints`, `validation`, `schema`, `vocabulary` and `example`;
- profile IRIs are versioned MAJOR.MINOR.

**The Workflow Run RO-Crate profiles, 0.6.0.** Released 2026-09-07,
including change #104, "Profile updates for RO-Crate 1.3" (page). Process
Run Crate is https://w3id.org/ro/wfrun/process/0.6. In its
`CreateAction`:
- `instrument` MUST be given;
- `name`, `description`, `agent`, `result` and `endTime` SHOULD be;
- `object`, `startTime`, `actionStatus`, `error` and `containerImage`
  MAY be;
- `environment` points to `PropertyValue`s.

The context https://w3id.org/ro/terms/workflow-run defines `sha256` and
`sha512` (fetched with curl).

**What certificates and provenance records carry** is already surveyed
in cft-fp256, docs/studies/CERT-V2.md, section 2, and reused here (READ).

**Quantum provenance.**
- **QProv** (Weder et al., IET Quantum Communication, 2021; its user
  guide; search). It covers IBM devices only.
- **QC-MM** (Huenchuleo, Sepúlveda and Fernández, *Applied Sciences*,
  2026, doi:10.3390/app16136346; search, abstract only). It has
  time-indexed calibration binding and transpilation traceability. Its
  abstract links compilation decisions to execution outcomes under
  different optimization settings: one cause, attributed within one
  experiment.
- **Peltonen, Stirbu, Mikkonen and Pautasso**, arXiv:2608.08272 (the HTML
  version, downloaded; page):
  - it finds "compilation provenance weakest";
  - it gives every value an evidence status;
  - a snapshot's association with an execution is qualified as
    provider-linked, configuration-linked, timestamp-matched,
    nearest-available or current-at-retrieval;
  - an adapter "may select" a timestamp-matched or nearest-available
    snapshot and record its difference in time;
  - a snapshot retrieved after execution, without historical validity,
    must not be presented as the state during it;
  - it names automated execution comparison among long-term ecosystem
    uses, not as a method it gives.
- **Stirbu and Meijer van de Griend**, arXiv:2608.05041 (abstract only;
  page). MLflow-style tracking of Qiskit's transpilation.
- **Kourousias et al.**, arXiv:2610.09931v2 (read in full: section 16).
  Fields a comparison must retain, and how precisely, for executions
  with matching records to agree within a declared tolerance. **Logan
  adopted its standard on 2026-10-14** (section 8).

**None of these attributes a difference between two runs to all its
causes, and none is an RO-Crate profile.**
- That is READ for Peltonen et al. and for Kourousias et al., who say of
  their guarantee that non-matching records "do not establish
  disagreement".
- For QProv, QC-MM and Stirbu and Meijer van de Griend, where only
  abstracts or search results were read, it is BELIEVED.
- That no other work attributes is BELIEVED, since the search was not
  exhaustive.

**IBM Qiskit Runtime:**
- SamplerV2 results carry `metadata["execution"]["execution_spans"]`, with
  start and stop "in UTC" (the ExecutionSpan reference; page).
- In the installed qiskit-ibm-runtime 0.50.0, `RuntimeJobV2.properties()`:
  - is documented as the properties "at the time the job started
    running";
  - is implemented as the backend's history snapshot nearest before the
    job's `running` time;
  - `IBMBackend.properties(datetime=...)` returns the one "closest to, but
    older than" the time given.

  That is a timestamp match made by the client, not a calibration the
  provider names for the job (base_runtime_job.py:199-214 and
  ibm_backend.py:325-376 in that version; READ).
- The runtime can also carry an optional `calibration_id`.
  - A backend can be built with one (ibm_backend.py:141-165). It is sent
    with the backend's configuration requests (:316) and history queries
    (:367), and with each job a primitive submits, in job mode as in a
    batch (base_primitive.py:155-208). All READ.
  - Peltonen et al. tabulate an IBM "calibration_id when present", and
    call it "optional" (READ). None of v0's 65 metrics files has one
    (section 4.3).
  - Whether IBM names a requested calibration in a job's records was not
    tested (question 9).

## 4. What Quantum-Film carries, and what IBM's own records add

READ, unless marked. Paths are in moth-quantum unless named otherwise.
The code-and-records survey read quantum_film/ibm/, quantum_film/atlas/,
fixer.py, compare.py, tools/hw_*.py, verify/run.sh, docs/VALIDATION.md
and every directory under docs/records/. Both verifiers recounted
section 4.1 and found it exact.

### 4.1 What is on disk

docs/records/ holds 13,114 files and 59,378,562 bytes:
- **2026-09-25 and 26, Atlas (Moth's platform, on its emulator: READ for the 2026-09-25 probes, by inference for the six law jobs; section 8):**
  - six jobs of the shelf's law circuit, `ed767c01…`, at 4,096 shots
    each;
  - 12,071 rolls, one per distinct layout;
  - a `commitments.jsonl` line per job, and the submit, status and result
    exchanges;
  - 85 files from about 22 earlier platform probes.

  Atlas returns per-setting counts, observables and density matrices,
  not shots.
- **2026-10-05, IBM:**
  - 31 bundles;
  - 65 jobs: 31 known-answer, 31 law and 3 coherence;
  - 68 device-run records, one per PUB;
  - 5 calibration snapshots;
  - 6 predictions.

### 4.2 The pipeline, stage by stage

| stage | what is recorded | how it is held | where |
|---|---|---|---|
| the question | the source circuit by SHA-256 (`ed767c01…`); each role's logical QASM, derived from it; the decode rule by name (`quantum_film.ibm.decode/v1`, `quantum_film.atlas.decode/v1`); the exact law | bundle.check refuses a circuit not derived from the source | bundle.py:111-129, 467-470; decode.py:34; compare.py:129-155 |
| the compile | target, level 2, seed 11, the chain, versions at the freeze; per circuit the QPY, a gate list and qasm3, each by SHA-256 | bundle.check holds each gate list to the law by the exact hold (isa.py) and SWAP-free five ways. It only hashes the QPY: the QPY's tie to its gate list is made at submission (tools/hw_run.py:197-201, with qiskit) | bundle.py:21-23, 424-507; isa.py:31-54, 301-326 |
| the submission | program `sampler` (SamplerV2), route `ibm-direct`, job mode; three option paths, their digest bound; `max_execution_time` | the options as sent must equal the manifest's | bundle.py:47-52; tools/hw_run.py:299-309 |
| the commitment | commitment v3, one per PUB, over its defining fields and a 32-byte salt, put in `circuit.metadata` | IBM echoes it in every PUB's result: 68 of 68 | fixer.py:144-146, 182-188 |
| the commit-before-read order | a marker before submitting; the line, holding IBM's created time, committed and pushed before any result is fetched | `git ls-remote` must equal HEAD; the line's commit is a strict ancestor of the raw result's, 65 of 65. A git order, REPORTED: rule 1 | anchor.py:49-96; audit.py:38-55 |
| execution | IBM's created, running and finished times (UTC, µs); QPU seconds; one execution span per job | REPORTED | `-metrics.json`, `-raw.json` |
| the raw result | IBM's results text, verbatim: per-shot bits in the order returned, which is not documented as the order the shots were taken | written before anything decodes it; byte-exact | raw.py:3-13; runner.py:309-316 |
| the records | device-run/v1: counts, role, basis, law, source, code, digest | canonical text; the digest recomputes | fixer.py:137-149, 448-494 |
| the controls | a known-answer job first in every bundle; ideal and noise-model predictions, seeded Aer samples, for the three morning bundles; baselines: the law, Atlas's shots, the twin; the sampler's floor | the audit requires the known answer first, and that it holds | decode.py:58-77; audit.py:131-144; compare.py:224-252 |
| the pre-registration | what runs, in what order, when to stop, what is measured | committed and pushed before any law job; later changes appended as dated notes | docs/PREREGISTRATION.md |

### 4.3 What it does not record

This table's states say what Quantum-Film's records hold: absent,
partial, unknown, unexposed or none. Three of them, `unknown`,
`unexposed` and `none`, are also rule 2's absence words, which a crate
writes (section 5). `absent` and `partial` are not.

| fact | state | evidence |
|---|---|---|
| the calibration in force when the shots ran | **absent from the records**; section 4.5 supplies what IBM's history returns | Snapshots run from 06:57:43 to 08:38:44Z, and the jobs from 10:26 to 12:58Z. `calibration_id` appears in 0 of 65 metrics files. |
| the local clock's offset from IBM's | **absent** | Line commits are dated 1.3 to 2.6 s before the IBM time they contain. git truncates to the second (section 4.4). |
| the code that ran | **partial** | Every record's `code` is "0.1.0", which has never changed (quantum_film/__init__.py:9). The run clones' commits appear only in docs/VALIDATION.md (lines 1614, 1689, 1695, 1698). |
| when each shot ran | **partial** | One execution span per job. The records drop the returned order. |
| readout error at execution | **partial** | Per-qubit values are in snapshots only. Each known-answer job prepares X on {0, 1, 3, 7, 12}, so it shows P(0\|1) on five qubits and P(1\|0) on eleven, confounded with its X gates. |
| the server's own settings | **unknown** | Only the three option paths are sent (bundle.py:50-52). rep_delay is 250 µs "on most backends" (research/2026-09-25/notes/moth-and-hardware.md:208), so it can differ by device. |
| a prediction's noise model | **partial** | Its stamp, seeds and versions are recorded, not the model. It repeats only on qiskit-aer 0.17.2 (tools/hw_predict.py:28-29). |
| Atlas's engine, seed and commitment | **unexposed**, or **none** | No seed exists on the platform (docs/VALIDATION.md:80-81). Its commitment is formed after the request returns a job id (tools/pauli_atlas_run.py:206-220), so the provider never held it. Its decode rule was inferred from the engine's output, then held to a known-answer run (quantum_film/atlas/decode.py:3-17). |
| the run scripts | **absent** | docs/VALIDATION.md:1626-1627 and 1694-1702 |

### 4.4 What the lead measured on the records

MEASURED by `v0_timing_and_drift.py` (section 15 gives its hash and
output):
- **Git truncates commit times to the second.** Measured with git 2.45.2
  on this desktop; draft 2's re-check confirmed it at fractional phases
  .02 to .995.
- **The local clock lagged IBM's.**
  - On ibm_kingston's first law job: more than 0.73 s by its line commit
    (made before 10:27:16Z, holding IBM's 10:27:16.731672Z), and more than
    0.93 s by its `fixed_at` against IBM's `finished`.
  - Over the day, under one constant offset: more than 1.58 s (the best
    of 65 line commits) and 1.68 s (the best of 68 records' `fixed_at`).
- **When the shots ran.** Read as UTC, every span lies inside [running,
  finished]: 65 of 65. From `running` to the first shot is 1.3 to
  192.2 s, median 1.7 s.
- **From known answer to law:** 19.4 to 297.3 s by created time, median
  21.4.
- **Which bytes stay equal.**
  - 17 of the 28 sheet law circuits' QPY bytes differ from the morning
    bundle's; no gate list does.
  - All 31 manifests carry one options digest and one program and route.
- **When each device ran.** No job of the day was interleaved: each
  device's jobs, of every role, form one block in the morning and one in
  the sheets, by created time.

  | device | morning block (3 jobs) | sheet block (all roles) | sheet law jobs |
  |---|---|---|---|
  | kingston | 10:26:56 to 10:30:29 | 12:21:21 to 12:37:20 | 8, from 12:22:18 |
  | marrakesh | 10:32:42 to 10:33:33 | 12:38:08 to 12:49:55 | 10, from 12:42:27 |
  | fez | 10:33:55 to 10:34:41 | 12:50:23 to 12:58:21 | 10, from 12:50:54 |

  Within marrakesh's block the five-crystal share steps +0.0306 between
  12:45:00 and 12:45:48.

### 4.5 What IBM's own records add (two reads, 2026-10-14)

**The reads.** Made with Logan's key, by Logan's word (decisions above).
- They were read-only, used no QPU time, and went through Quantum-Film's
  own `account` and `keyleak` modules.
- The key and the CRN were neither printed nor written.
- records/2026-10-14/README.md gives the runs, failures included, and
  the manifests' hashes.

**The anchors, and the submission as IBM holds it** (`ibm_refetch_v0.py`;
MEASURED). For all 65 jobs:
- IBM's created time equals the job line's;
- all 68 PUBs' commitments, inside IBM's own copies of the submitted
  circuits, equal the lines';
- every circuit IBM holds, read through Quantum-Film's `isa.gate_list`,
  equals its bundle's frozen gate list, layout included. That closes, for
  v0, the QPY-to-gate-list tie the exact hold does not make (R12);
- options and shots equal the manifests'.

**The raw bytes** (`ibm_results_refetch_v0.py`; MEASURED). For all 65
jobs, IBM's results text today is byte for byte the committed raw result.

**The calibrations** (`calibration_at_execution_v0.py`; MEASURED). These
are the snapshots IBM's history returned for a query at each job's first
shot. Each is compared with the morning bundle's freeze:

| device | snapshot | first shots | values differing from the morning freeze | on the device's 16-qubit chain: readout, T1, T2 and CZ error |
|---|---|---|---|---|
| kingston | 09:02:46Z | the 3 morning | 0 of 6,211 | none |
| kingston | 11:28:27Z | 10 | 342 | readout and T1/T2 unchanged; CZ errors moved by a mean of +0.0003, the largest by 0.0024 |
| kingston | 12:21:18Z | 6 | 680 | the same chain changes |
| marrakesh | 09:51:18Z | the 3 morning | 2 of 6,230 | none |
| marrakesh | 11:21:28Z | 20 | 2 of 6,230 | none |
| fez | 10:08:31Z | the 3 morning | 0 of 6,203 | none |
| fez | 11:44:47Z | 20 | 0 of 6,203 | none |

Each device's sheet bundles were frozen against a later snapshot:
- kingston's 8 against 11:05:15Z, which no record carries;
- marrakesh's 10 against 09:51:18Z, and fez's 10 against 10:08:31Z. Each
  equals, value for value, the snapshot in force for those sheets.

**What these establish:**
- **The stamps are not the content.**
  - Against the morning freeze, each execution-time snapshot carries a
    different measurement date on 1,922 to 3,316 values.
  - Five of them were returned for kingston's morning jobs and for all
    of marrakesh's and fez's. Those five re-date 1,922 to 1,984 values
    each, and change at most 2.
  - The 2 on marrakesh are one coupler's `rzz` error, listed in both
    qubit orders, which rose from 0.0029 to 1. Marrakesh's circuits do
    not use that coupler.
  - These counts cover the qubit and gate values. The snapshots' 449
    `general` and 97 `general_qlists` entries show no value difference
    either (draft 4's re-check).
  - Each snapshot holds values measured 2.2 to 4.0 minutes after its own
    stamp.
  - So a calibration is identified by a digest of its values, and its
    link to a job also checks the newest measurement date inside it
    (section 6).
- **The history can return a snapshot minutes after its stamp.**
  - 12:21:18Z was not returned for a query 9.0 minutes after its stamp,
    and was returned for one 9.4 minutes after it (MEASURED).
  - That is the only snapshot of the seven whose lag the read's queries
    bound from below. The other six are bounded only from above, by 25
    to 84 minutes.
  - So 8 kingston jobs whose first shots fell between 12:26:17 and
    12:29:52Z were linked to 11:28:27Z, although 12:21:18Z was already
    stamped and fully measured. Which of the two was in force for them
    is not known.
  - That the history is keyed by when a snapshot was stored is BELIEVED.
- **Kingston's calibration moved during the day; fez's did not.**
  - Against the morning freeze, kingston's sheets ran under 342 or 680
    changed values, among them the CZ errors on its chain. That holds
    whichever of the two snapshots was in force for the 8 jobs above.
  - Their own freeze, 11:05:15Z, is in no record, so the change since it
    is not measured.
  - Marrakesh's and fez's sheets ran under values equal to their sheet
    freezes.
- **`properties()` answers for the job's `running` time, not its first
  shot.** For one job, kingston's known answer `db1pgmjid5ic73erg1u0`,
  the history returned 11:28:27Z at `running` and 12:21:18Z at the first
  shot.
- **The morning predictions were built from the values in force.**
  - Marrakesh's and fez's were built from later snapshots than their
    freezes, 08:32:46Z and 08:38:44Z, value for value equal to those
    freezes.
  - Against the snapshots in force, 0 values differ on kingston and fez,
    and 2 of 6,230 on marrakesh.
  - So "every prediction was kinder than its device"
    (docs/HARDWARE-RESULTS.md:56) is not a stale-calibration effect, as
    far as IBM's reported values go.
- **Quantum-Film's results document overstates one point.**
  - docs/HARDWARE-RESULTS.md:194 says "kingston recalibrated between its
    bundle's freeze (06:57:43Z) and its run".
  - For the morning run, the values IBM reports did not change; the
    stamp and 1,956 per-value dates did.
  - Kingston did recalibrate later in the day: its sheets ran under 342
    or 680 values changed since 06:57:43Z.
  - That is recorded in this repository, not edited there.
- **The readout inputs were old.** The coherence pair's readout values
  were measured 7.1 h (kingston), 7.8 h (marrakesh) and 10.5 h (fez)
  before their coherence jobs were created.

## 5. Rules for deciding a field

PROPOSED. Rules 1 to 4 are cft-fp256's (docs/studies/CERT-V2.md section
4, READ), with rule 1 extended and rule 4 made explicit. Rules 5 to 9 are
new.

1. **Checked, read, anchored or reported.** Every field says which.
   - **CHECKED:** the checker re-derives it from the crate.
   - **READ:** the checker's arithmetic takes it as given, so a false
     value fails its own re-derivation (the decode's bit order, tested by
     the known answer).
   - **ANCHORED:** a value bound by a record the producer does not
     control, as established by fetching that record from its holder.
     - Quantum-Film's commitment rides in `circuit.metadata`, which "goes
       inside the submitted job's parameters, which IBM keeps with the
       job's server-set `created` time, unless the job is private or its
       owner deletes it" (moth-quantum, docs/HARDWARE.md:79-83, READ).
     - So ANCHORED needs a re-fetch with the owner's key, while the
       provider keeps the job. Until then the field is REPORTED, with its
       holder named.
     - A git commit is never an anchor: its time is the local clock's.
     - v0's IBM fields were anchored on 2026-10-14 (section 4.5).
   - **REPORTED** otherwise: "stated, not checked".
2. **Absence has words:**
   - `unknown`: not recorded;
   - `none`: does not exist for this device or route;
   - `withheld`: the producer has it and chose not to publish it;
   - `unexposed`: the provider gives it to nobody.

   The first three are cft-fp256's; `unexposed` is added.
3. **Identify the run, not the person.**
   - **Carried:** job identifiers, device names, the plan, and public
     repository URLs as provenance (Quantum-Film's bundle READMEs name
     its public repository). A contribution, an audit record or a custody
     log may also carry a public handle its author chooses (sections 9.1
     and 9.2).
   - **Never carried:** the API key, the instance's CRN, the provider's
     account and user identifiers (IBM's job document has a `user_id`,
     which the reads omitted), local host and user names, and local
     paths.
4. **Reproducible bytes stay reproducible.**
   - **The header** holds what two writers make differently: the writer
     and its version, the time of writing, implementation versions,
     RO-Crate's `datePublished`, and the signature and trusted-time slots
     (section 9). `datePublished` "MUST be a single string value in ISO
     8601 date format" (RO-Crate 1.3, READ by the re-check).
   - **The body** holds what the run is and what the definitions compute.
   - The checker normalises the header before it compares bytes.
5. **One fact, one place.** `ro-crate-metadata.json` is generated from
   the records. The checker regenerates it and compares bytes. It is
   never written by hand (HonestFramework, METHOD.md section 4).
6. **Raw before adjusted.**
   - A raw result is its own entity, fixed before anything decodes it.
   - An adjusted value is a separate entity that names it.
   - This is cft-fp256's "one format, one meaning"
     (docs/studies/CERT-V2.md:1038-1042), and Quantum-Film's "exploratory
     … beside the pre-registered tables, never in their place"
     (moth-quantum, docs/PREREGISTRATION.md:277-279). Both READ.
7. **Counts are paid for.** A shot count is the number of shots the raw
   entity holds, never a number stated beside it (cft-fp256,
   docs/CERTIFICATES.md:975-1015, READ).
8. **A random choice the producer could grind belongs to the checker, or
   to nobody.**
   - Every simulated reference is keyed only by what the question fixes
     before any run: the law, the count, the measure set.
   - v0's floor complies: `stream("compare-floor", stock, n, r)`.
   - v0's seeded Aer predictions do not, so they are REPORTED
     references, never controls.
9. **Every field carries its kind as data.** The vocabulary table gives
   each term its kind, and a value may weaken it only with an absence
   word. "An unenforced marker decays to prose within one round"
   (HonestFramework, METHOD.md section 8, READ).

## 6. The causes of a difference

PROPOSED. For each cause, what the crate carries to hold it.
- **The statuses** are EQUAL, DIFFERS, CONTROLLED and UNMEASURED. An
  UNMEASURED status carries its absence word.
- **CONTROLLED** means a certified bound on the cause's effect on the
  measure exists, under a named model where one is needed (R5, R6).
  Measuring the cause is not enough. Whether the bound is tight enough
  is the strong form's question (section 8).
- **Each cause gets one status per measure.** What both runs share is
  listed as unseen (section 8).

| cause | what it is | held by | v0, IBM | v0, Atlas |
|---|---|---|---|---|
| 1. the question | logical circuits, observables, decode rule, measure set, law, twins | EQUAL by digest, or `question-differs` | EQUAL across all IBM bundles | the same source circuit; a different decode rule, so IBM against Atlas is `question-differs` |
| 2. the compile | the circuits sent | EQUAL by gate-list digest, with each gate list tied to the circuit the provider holds (rule 1). Where the compiles differ, the comparison states DIFFERS, logically equivalent by the exact hold. The noisy effect of different circuits on different qubits is then part of the device's realization: the hold bounds nothing about noise | each device's gate lists are byte-identical across its bundles; kingston's, marrakesh's and fez's differ (257, 251 and 249 sx gates; 102 CZ each). IBM's copies equal them | `unexposed` |
| 3. what was submitted | program, route, mode, options, shots, and the producing kit's commit | EQUAL by digest of what was sent, and, once anchored, of what the provider holds | EQUAL in what was sent: one options digest, program and route in all 31 manifests, and IBM's copies agree. The producing commit is `unknown` per job; docs/VALIDATION.md names the run clones' commits (section 4.3) | the request body; the producing commit is on every line, as `code_commit` (question 9) |
| 4. the sampling | the shots' randomness | CONTROLLED always, by the named concentration inequality (section 8) | CONTROLLED | CONTROLLED, under the same independent-shots model; its sampler is `unexposed` |
| 5. readout | what measurement does to the prepared state | CONTROLLED for a measure only by readout controls covering its qubits in both directions, in the job or the job just before it on the same device (section 9), with a stated confusion model (kind `conditional`). Bit order is a precondition, not a status: a known answer holds it, or the checker refuses (`known-answer`) | readout UNMEASURED, `none`, for every measure; bit order held in every bundle | readout `none`; bit order held to a frozen vector |
| 6. the device's and provider's state, and when | the calibration in force, the qubits, the server's settings and software, and the time block | REPORTED, with the calibration's link (below). Device is separated from time only by interleaving | calibrations linked `history-at-first-shot`, 8 of them `history-in-gap` (section 4.5); server settings `unknown`; no job interleaved: each device's jobs ran in their own blocks | `unexposed` |
| 7. drift within a run | the device moving between and within its jobs | CONTROLLED only by a certified bound U(D) on how far any job sits from its run's mean (section 8). It needs repeats; whether it is tight enough is the strong form's question | law role: CONTROLLED, 9, 11 and 11 jobs a device, though two runs' bounds together exceed the difference (section 6.1); coherence role: UNMEASURED, `none` (one job a device) | 6 jobs, no spans |

**The calibration link.** It is PROPOSED, revised by the reads of section
4.5. A calibration is identified by the SHA-256 of its values, with every
date excluded, so two snapshots with equal values are EQUAL whatever
their stamps. A job's link is chosen in this order:
- `provider-linked`, where the provider names a calibration;
- otherwise `history-in-gap` or `history-at-first-shot`, from the history
  at the first shot;
- otherwise `read-before-run`, `read-after-run` or `unknown`.

`history-at-running` is carried beside the link. The terms are:
- `provider-linked`: the provider names the calibration the job ran
  under. For v0, IBM's records do not: no metrics file carries a
  `calibration_id` (section 3).
- `history-at-first-shot`: the snapshot the provider's history returns
  for a query at the job's first shot. Its stamp and its newest
  per-value date are checked to precede that shot.
- `history-in-gap`: as `history-at-first-shot`, but another snapshot the
  crate carries was already stamped and fully measured before the shot,
  and the history had not yet returned it.
  - The link names both. Neither is presented as the one in force.
  - 8 of v0's 65 jobs (section 4.5).
- `history-at-running`: what `properties()` returns, the history at the
  job's `running` time. It differs from the history at the first shot on
  1 of v0's 65 jobs.
- `read-before-run`: read at a freeze or before submission.
- `read-after-run`: read after the shots, and never presented as the
  state at execution.
- `unknown`.

The history can return a snapshot minutes after its stamp (section 4.5). So
every `history-` link is a necessary condition for being in force, not a
proof.

**Clocks are named.** Every time field states its clock, `provider` or
`local`. An order across the two is REPORTED unless the crate carries a
measured offset.

**Drift is stated in units the count cannot inflate.** HonestFramework:
"State a threshold in units the corpus cannot inflate" (METHOD.md:523,
READ).
- The certified statement is U(D) (section 8).
- The between-run SD, with its degrees of freedom, is an estimate stated
  beside it.
  - At the floor of three repeats it has two degrees of freedom. Its 95%
    interval then runs from 0.52 to 6.29 times the estimate (the
    re-check's figure).
  - That is why U(D), not the SD, decides CONTROLLED.
- An observed min-max range grows with the count of runs, and is never
  stated as the drift.
  - U(D) is a maximum too, because the strong form's claim, every job
    against every job, needs one.
  - Its intervals hold together over the whole family. So adding jobs
    cannot raise the chance of a false claim: it widens every interval
    instead.

### 6.1 Worked example: ibm_kingston against ibm_fez, on v0's data

**How the figures were made:**
- `isolation_v0.py` gives the certified verdicts, and
  `v0_timing_and_drift.py` the estimates. Both are MEASURED.
- The known-answer rates and the chains are READ from
  docs/HARDWARE-RESULTS.md and the manifests.
- The coherence estimates are READ from docs/HARDWARE-RESULTS.md:46.

**The runs.** The campaign of 2026-10-05, selected by device: kingston's
law and coherence jobs against fez's.

**The declaration.** This study chose the selector and the tolerance
after v0's data were read, so the comparison is exploratory
(`selector-late`). It is declared real: both runs are `qpu`. It uses
ε = 0 for every measure, the weakest claim:
that the two differ at all. At ε = 0 no measure can be certified to
agree, so each verdict is differ or unresolved.

**The causes.** Each has one status per measure. Only drift's status
differs between measures.
- **the question:** EQUAL;
- **the compile:** DIFFERS, logically equivalent by the exact hold.
  The chains [20, 21, 36, …] and [140, 141, 142, …] differ, and so do
  the gate lists;
- **what was submitted:** EQUAL in what was sent, as IBM holds it. The
  producing commit, which cause 3 now includes, is `unknown` per job for
  v0; docs/VALIDATION.md names the run clones' commits (section 4.3). So
  this EQUAL covers what was sent;
- **the sampling:** CONTROLLED, by the certified intervals below;
- **readout:** UNMEASURED, `none`: no readout control covers the measured
  qubits in both directions.
  - Bit order, the precondition, is held. The known answers read
    90.3–92.1% on kingston and 86.4–90.6% on fez, with none on the
    mirror;
- **the device's state and time:** DIFFERS. That covers:
  - the devices;
  - the calibrations in force, REPORTED and linked
    `history-at-first-shot`, 8 of kingston's `history-in-gap`.
    Kingston's moved since its morning freeze, and fez's did not;
  - the time blocks: each device's jobs ran in their own blocks
    (section 4.4);
- **drift:**
  - for the three law measures, CONTROLLED by U(D) below, though the
    two runs' bounds together exceed the difference;
  - for the two coherences, UNMEASURED, `none`: one job each.

**Unseen, because both runs share them:** the decode, the bundle design,
the known-answer pattern, and the date. Both ran on 2026-10-05, though in
different blocks.

**The certified verdicts.** α = 0.05 over a family of 70 intervals.
Hoeffding's KL bound for means of independent [0, 1] variables.
Conditional on independent shots.

| measure | class (uniform / dephased twin) | day means, certified | drift bounds U(D), kingston / fez | strong form: L(\|diff\|) − U(D_A) − U(D_B) | isolated from the pipeline? | isolated as quantum? |
|---|---|---|---|---|---|---|
| five-crystal share | integrity / integrity | **differ**: kingston − fez in [+0.0438, +0.0598] | 0.0307 / 0.0323 | −0.0193: drift not excluded | no: strong form not above ε; producing commit `unknown` | no: not isolated from the pipeline; readout UNMEASURED, `none`; integrity against both twins |
| forbidden share | signal / integrity | **differ**: in [−0.0130, −0.0040] | 0.0123 / 0.0138 | −0.0220: drift not excluded | no: strong form not above ε; producing commit `unknown` | no: not isolated from the pipeline; readout UNMEASURED, `none`; a signal against the uniform twin only |
| linear XEB | signal / integrity | **unresolved**: [−0.0471, +0.0783] | 0.1575 / 0.1650 | −0.3225 | no: strong form not above ε; producing commit `unknown` | no: not isolated from the pipeline; readout UNMEASURED, `none`; a signal against the uniform twin only |
| ⟨X0X1⟩ | signal / signal | **unresolved**: [−0.0562, +0.1809] | UNMEASURED, `none` (one job each) | — | no: drift UNMEASURED, `none`; producing commit `unknown` | no: not isolated from the pipeline; readout UNMEASURED, `none` |
| ⟨Y0Y1⟩ | signal / signal | **unresolved**: [−0.0931, +0.1428] | UNMEASURED, `none` | — | no: drift UNMEASURED, `none`; producing commit `unknown` | no: not isolated from the pipeline; readout UNMEASURED, `none` |

**The estimates beside them**, which are not verdicts:
- in between-run SDs, with equal weights (df-weighted in brackets):
  - five-crystal share: +5.18 SDs (+5.23), Welch t +11.4;
  - forbidden share: −3.56 SDs (−3.50), Welch t −8.1;
  - XEB: +0.94 SDs (+0.93), Welch t +2.1;
- ⟨X0X1⟩: +0.0625 between single runs, about 3 sampling errors;
- under the readout model (kind `conditional`, on the snapshots in force,
  whose readout values were 7 to 10.5 h old), readout alone would explain
  +0.0034 of that gap. That is the model acting on the law's values,
  whose single-site means are 0, so its cross terms vanish (section 9.1).

**What this says on v0's own data:**
- The devices' day means **differ**, certifiably, in integrity and in
  the forbidden share.
- Under the adopted standard, nothing is isolated from the pipeline: no
  measure's difference clears the two runs' drift bounds, and the
  producing commit is `unknown` (section 8). So nothing is isolated as
  quantum.
- Had a difference cleared them, it would be the device's-and-its-time's,
  not the device's alone.
  - Every job ran in its device's own block.
  - Kingston's calibration moved during the day while fez's did not
    (section 4.5).
- The parametric estimates are larger than the certified margins.
  - They assume normal sampling across jobs.
  - The certified bounds assume only independent shots, and hold for
    all 70 intervals at once.
- **This is v0's limit, and the next run's design (question 9).**
  - The drift bounds are wide partly because each job has only 24,576
    shots, and partly because the jobs did move (section 4.4).
  - The time block is confounded because no job was interleaved.

## 7. The measures: signal or integrity, decided by the authority

**The rule** (PROPOSED). Each measure's expected value is computed under
the law and under a named classical twin T. These are quantities free of
the shot count.
- **Signal against T** when they differ, with the quantum range [T(m),
  law(m)].
- **Integrity against T** when they agree. A fault shows in the measure,
  but a classical sampler of the same law would score the same.
- The class is computed by the authority, never declared
  (`measure-class`, section 11).

**Two twins** (PROPOSED):
- **the uniform twin:** five distinct sites of sixteen at random,
  Quantum-Film's "twin";
- **the dephased twin:** the law's own layout distribution with every
  coherence removed. This is the model behind Quantum-Film's coherence
  argument, "A classical mixture with the same layouts gives 0"
  (docs/PREREGISTRATION.md:250-251, READ).

A comparison's "isolated as quantum" names its twin. Against the uniform
twin, the claim is a **distribution signal**. Against the dephased twin,
it is a **coherence signal**, the only one that no classical sampler of
the law's distribution gives (the re-check's note on D2).

| measure | law | uniform twin | dephased twin | class: uniform / dephased |
|---|---|---|---|---|
| N-crystal share | 1 | 1 | 1 | integrity / integrity |
| one-site occupations | 5/16 each | 5/16 each | 5/16 each | integrity / integrity |
| forbidden share | 0 | 85/273 | 0 | signal / integrity |
| TVD to the law (population) | 0 | 85/273 | 0 | signal / integrity |
| linear XEB | +1 | 0 | +1 | signal / integrity |
| pair occupations | the law's | the uniform's | the law's | signal / integrity |
| NN pair correlation | 16/25 | 64/75 | 16/25 | signal / integrity |
| ⟨X0X1⟩, ⟨Y0Y1⟩ | +3/8 | 0 | 0 | signal / signal |

The law and uniform-twin values are READ (moth-quantum,
docs/HARDWARE-RESULTS.md:35-47, and compare.py). The dephased column
follows from the definition, and is BELIEVED until v0's authority
computes it. The crystals per shot are an integrity measure by the same
rule.

**Estimators.**
- **Unbiased means:** the shares, XEB (a mean of P(Y)) and the coherences
  are means of per-shot variables, unbiased. The forbidden share and XEB
  are means over the five-crystal shots, unbiased given how many there
  are.
- **The NN correlation** is a ratio of counts. It is approximately
  unbiased at these counts: the re-check simulated a bias of +0.00002 at
  24,576 shots, and −0.0011 at 200 (R11).
- **Statistics:** one-site and pair max |z| grow as the square root of
  the count, and the sampled TVD has a floor. They are statistics,
  reported and never placed in a range.

**Values and uncertainty** (cft-fp256's kinds, docs/CERTIFICATES.md:698-705,
READ, applied to shots):
- **A measure's value is a measurement of the run:** an exact function of
  the shots, CHECKED, stored as the exact ratio of whole counts.
  Quantum-Film's compare.py keeps XEB exact, and computes TVD exactly but
  stores it, and the shares, as floats (compare.py:290-304 and 340-361).
- **Its certified interval** is a new kind, `certified`, proposed here
  (section 8). It is a bound holding with probability at least 1 − α
  over a stated family, under a named sampling model and a named
  inequality.
- **Its ± from a normal approximation** is an `estimate`, stated beside
  the certified interval and never in its place.

## 8. The comparison, under the adopted standard

**Logan adopted Kourousias et al.'s standard on 2026-10-14.**
- Its supplement (S1.6) allows a declared comparison to replace the
  Hellinger distance between outcome laws with the absolute difference of
  a bounded observable's mean, in that observable's own units.
- That is the form used here for the measures of section 7. The Hellinger
  form remains for declared outcome laws (section 16.5).
- Everything else in this section is PROPOSED.

**What a comparison declares, before any data are read:**
- its two runs, each a crate and a selector over its jobs (device, role,
  bundle, date), or a set of crates with selectors (section 9.1);
- whether it is real or a rehearsal (refusal 4, below);
- for each measure:
  - its distance: Hellinger on a declared outcome law, or the absolute
    difference of a bounded mean;
  - its tolerance ε, in those units;
- its confidence 1 − α over the comparison's whole family of intervals,
  by a union bound;
- its concentration inequality:
  - Hoeffding's KL form for means of independent [0, 1] variables. That
    covers a device-day's pooled shots. Their target is the mean of the
    jobs' means, each weighted by the job's shots in scope: for the
    forbidden share and XEB, its five-crystal shots;
  - the Agrawal radius of the paper's Eq. (12) for outcome laws;
- its sampling model: independent shots within a job, and independent
  jobs.

**What it refuses before computing any value:**
1. **`comparison-trivial`:** the two runs share a job of a role the
   comparison measures, by job id, commitment or raw digest.
   - A resealed copy shares them, so it is refused.
   - Two runs may share a control job, such as a known answer, without
     this refusal.
2. **`question-differs`:** the question's digests differ, and the
   comparison has not declared the question as the factor it varies. IBM
   against Atlas meets this.
3. **`role-missing`:** a measure needs a role one run lacks. That
   measure is refused by name, and the comparison goes on to the others.
4. **`kind-not-qpu`:** a comparison declared real, with a run holding a
   unit or crate of kind `simulator`. Every comparison declares itself
   real or a rehearsal (section 13, stage 4).
   - A rehearsal may pool `simulator` units. It says so in its body, and
     is never cited as a result.
   - v0's Atlas crate is kind `simulator`. Its six law jobs' records carry
     no `mode` (draft 10's re-check), so the kind rests on facts READ in
     moth-quantum, and an inference:
     - the throwaway key's account had `features: []`: "So **no
       `run_quantum`** (hardware)" (docs/VALIDATION.md:19-27);
     - the six law jobs were that account's (docs/VALIDATION.md:925,
       1063-1064 and 1097);
     - their request names no `provider_name`
       (quantum_film/atlas/pauli_tile.py:143-145), and the engine's
       default is `aer`, in its description fetched on 2026-09-25 (under
       docs/records/2026-09-25/atlas/);
     - so, by inference, they ran on Moth's emulator.

     VALIDATION.md's two entries of 2026-09-25 say so of their own jobs:
     "Every job ran on `emu`" (:21-22), and "All of it is `emu`" (:250).
     The 20 `mode` values under docs/records/2026-09-25/atlas/, from 8
     probe jobs, are all `emu` (draft 9's and draft 10's re-checks).
   - So IBM against Atlas is a rehearsal by kind, and `question-differs`
     by its decode.
5. **`selector-late`:** a selector or tolerance not declared before the
   data were read.
   - A pre-registration that names it, or a comparison crate committed and
     anchored before the runs' results, establishes it.
   - Otherwise the comparison is labelled exploratory, not refused.
     Quantum-Film's rule is to show such work "beside the pre-registered
     tables, never in their place".

**What it computes, for each measure:**
- each run's certified mean (or law), and the certified difference
  [L, U];
- each run's drift bound U(D): the largest certified distance of any one
  job's mean from its run's mean;
- **the strong form,** L(|diff|) − U(D_A) − U(D_B). When it exceeds ε,
  every job of one run differs from every job of the other by more than
  ε;
- for each cause of section 6, one status per measure: EQUAL, DIFFERS,
  CONTROLLED (with the control and its result) or UNMEASURED (with its
  absence word);
- as unseen, what both runs share.

**Its verdicts:**
- **the runs' means:** **differ** if L(|diff|) > ε; **agree** if U(|diff|)
  ≤ ε; otherwise **unresolved**;
- **isolated from the pipeline:** all of the following hold;
  otherwise the statement names every one that stopped it:
  - the question and what was submitted are EQUAL. The producing
    commit counts as EQUAL only where it is recorded; where it is not,
    the statement names `unknown`;
  - the compile is EQUAL, or DIFFERS but logically equivalent;
  - bit order is held;
  - the strong form exceeds ε.

  It also says whose the difference is: the device's, where interleaving
  separates device from time; otherwise the device's-and-its-time's.
- **isolated as quantum:** the first holds, and the measure is a signal
  against the named twin (section 7).
  - Readout's effect must also be bounded below the margin: the strong
    form, less a readout bound ρ, still exceeds ε.
  - ρ is certified from readout controls covering the measure's qubits
    in both directions, in the job or just before it (section 9's
    levels), under a stated confusion model. So the statement carries
    the kind `conditional`.
  - For a difference, ρ takes the shrinkage of the device that reads
    lower, plus both devices' offsets (section 9.1).
  - A difference of means less ρ ("beyond readout") is not yet this
    statement, which needs the strong form less ρ.

It passes and fails no run: "The comparison measures; it never passes or
fails a run" (moth-quantum, docs/PREREGISTRATION.md:79-80, READ). Its
verdicts are about the difference between two runs, at a declared
tolerance.

**Why the strong form.** A difference of means alone could be a few jobs
on one device moving. The strong form needs every pair of jobs to be
separated, and drift within each run bounded, which is what "CONTROLLED"
means for drift (R5).

**Pooling units across crates,** with verdicts that stay valid as units
arrive, is in section 9.1.

**What it cannot see:**
- **What both runs share.** A difference cancels whatever both runs
  carry. cft-fp256 found the same in its own estimates: "The half-step
  run halves h/6 exactly and the wider run widens it exactly, so neither
  sees it" (docs/studies/ACC-A-estimates.md:54-62, READ). Everything
  both runs share is listed as unseen.
- **What differs with the device.** A cause that differs together with
  the device, such as v0's time block, is named. It is not separated
  except by interleaving.
- **A fabricated run with fresh identities.** It needs fresh job ids,
  salts and commitments, so it evades `comparison-trivial`. Only the
  anchor's re-fetch from the provider exposes it (rule 1).
- **A per-field tolerance check composed by hand.** The paper shows
  independent full-tolerance thresholding can fail to compose, while a
  summed bound is valid on a Cartesian context set (its S1.4). This
  comparison never certifies from per-cause tolerances: its verdicts are
  computed on the runs' own data, so the failure the paper shows cannot
  arise. The control `joint-omission` holds it to that.

**What it proves, and what it does not.**
- **Proves**, at the stated confidence and under the stated sampling
  model:
  - every verdict;
  - that every EQUAL cause is byte-identical;
  - every control's result.
- **Does not prove:**
  - that a REPORTED calibration was in force;
  - anything about what both runs share;
  - that the sampling model holds: shots independent and jobs
    independent;
  - that a `conditional` model is right;
  - that the selector was chosen before the data were seen, unless a
    pre-registration or an anchored comparison crate shows it
    (`selector-late`);
  - which physical mechanism made a difference.

## 9. The crate

PROPOSED throughout.

**Three words:**
- **A crate** holds one contribution: one free-tier unit (section 9.1),
  v0's IBM campaign, or v0's Atlas runs.
- **A campaign** is what one pre-registration fixes. It is one crate for
  v0. For the free-tier unit it is every unit under the standing
  pre-registration, so many crates.
- **A comparison** is a crate of its own. It names its runs by each
  crate's metadata-body digest and selector, and may pool many crates.

v0 makes two crates:
- the IBM campaign of 2026-10-05;
- the Atlas runs of 2026-09-25 and 26. These had no pre-registration,
  which the crate says with `none`.

**Inside a crate:**
- RO-Crate 1.3, conforming to Process Run Crate 0.6 and to this profile;
- Quantum-Film's files keep their own relative paths, copied byte for
  byte, each held to the pinned submodule by digest;
- the reads of section 4.5 are carried as dated provider records.

| entity | RO-Crate type | what it holds | kind |
|---|---|---|---|
| the root | `Dataset` | `conformsTo` Process Run Crate 0.6 and QRO-Crate 0.1; `mentions` every action; licence, CC BY 4.0; `datePublished` (header); `qro:signature` and `qro:trustedTime`, in the header so that signing never changes the crate's identity, and `none` in v0 | (the record) |
| the question | `CreativeWork`, `qro:Question` | the logical circuits, law table, twins, decode rule, and the measure set's definition and version | CHECKED |
| the pre-registration | `CreativeWork` | the file as committed, its commit and push | REPORTED |
| a device | `IndividualProduct` | name, processor, qubits; `qro:deviceKind` | REPORTED |
| a bundle | `Dataset` | the manifest, the bundle's identity; the frozen circuits | CHECKED |
| a compile | `CreateAction` | the transpiler at its version; logical circuits, snapshot, level and seed; the frozen circuits; the exact hold's verdict | CHECKED (step 7) |
| a calibration snapshot | `File` | the provider's text; its values-digest; `qro:calibrationLink`; stamp; when read | REPORTED |
| a prediction | `CreateAction` | the simulator, circuits, snapshot and seed; counts and measures | REPORTED: a seeded reference |
| a job | `CreateAction` | the provider's program; `qro:device`; circuits, options and shots; the raw result; the job id; `startTime` and `endTime` with their clock; per-PUB `qro:role` and `qro:commitment`; the job line and its commit; the producing kit's commit | REPORTED, and ANCHORED once re-fetched |
| a raw result | `File` | the provider's bytes, verbatim | CHECKED by digest; ANCHORED once re-fetched |
| a provider record | `File` | a dated re-fetch: IBM's job document (with no `user_id`), metrics, or result digests | REPORTED, with the holder and date |
| a decode | `CreateAction` | the decode rule; the raw result; the records | CHECKED |
| the measures | `CreateAction` | the measure set's definition, version in the body and implementation in the header; records, law and twins; values, classes and certified intervals | CHECKED |

**Canonical bytes:**
- ASCII, sorted keys, a fixed indent, LF line ends, and a final LF;
- `@graph` order: the descriptor, the root, then everything else by `@id`
  (order is "not significant" in RO-Crate 1.3);
- **no JSON number except a non-negative integer.** Every other quantity
  is a string in one spelling (cft-fp256, docs/CERTIFICATES.md:175-227,
  READ):
  - a rational as `N/D` in lowest terms;
  - a digest as 64 lowercase hex digits;
  - a binary64 as its 16 hex digits and its exact decimal;
  - a time as RFC 3339 UTC with `Z`;
  - `datePublished` as an ISO 8601 date;
  - `contentSize` as a decimal count of bytes.

The strict reader refuses other spellings (`spelling`), unknown terms
(`term-unknown`) and fields with no kind (`field-kind`). Quantum-Film's
own files are data entities, kept as they are.

**Validation runs in two layers:**
- **the profile's SHACL shapes**, under rocrate-validator's `must/`,
  `should/` and `may/`, run by rocrate-validator or any SHACL engine;
- **QRO-Crate's checker**, for everything the shapes cannot express.

**Levels.** A ladder of what a crate carries; each level is the one below
plus more. The comparison's verdicts are separate: they depend on the
data, and a crate at any level can yield "unresolved".
- **recorded:** every cause of section 6 is held or named with an absence
  word, and everything CHECKED re-derives.
- **anchored:** in addition:
  - every job's commitment has been found in the provider's own copy;
  - every circuit the provider holds has the held gate list;
  - every raw result equals the provider's copy.

  Each of these is a dated re-fetch.
- **comparable:** in addition:
  - every role a comparison will measure has at least three jobs a
    device;
  - every bundle holds bit order by a known answer, not merely naming it
    absent;
  - every gate list is exposed and passes the exact hold;
  - the crate's devices are interleaved in time;
  - the shots per job meet the planning rule for the tolerance the
    pre-registration names (section 16.5).
- **quantum-comparable:** in addition, readout controls cover, in both
  directions, every qubit a measure reads. They sit in the same job, or
  in the job just before it on the same device, linked to a calibration
  with the same values-digest.

**Where v0 stands:**
- **The IBM crate is anchored** (section 4.5). It is not comparable: none
  of its jobs is interleaved, its coherence role ran once a device, and
  its shots per job are short of the planning rule.
- **The Atlas crate is recorded.** Its provider never held a commitment.

### 9.1 The free-tier unit: a run anyone can repeat

**The aim,** in Logan's words (2026-10-14, verbatim): "Ideally we can size
a run that can be repeated by anyone on a free tier to give adequate data,
allowing anyone to contribute more runs of the same thing for no cost.
I'll still run multiple batches myself when the free quota refreshes".

**Labels.**
- Everything below is PROPOSED, except where it says READ or BELIEVED.
- Its figures are MEASURED by `free_tier_unit_v0.py` on v0's records.
- Where they project a new unit, they take as its truth:
  - v0's per-device means and its largest job-to-job deviations;
  - v0's largest within-device Hellinger distance R, 0.0335 on the
    three-way class;
  - v0's coherence values and the pair's single-site means. Each comes
    from one 4,096-shot PUB a device, so each carries a sampling error of
    about 0.015;
  - the readout errors IBM reported at v0's freeze.
- That is a projection, not a measurement of any new run. The
  projections for coherence differences are rough, because of the
  single-job values they start from.

**The free tier:**
- 10 QPU-minutes per rolling 28 days, in us-east, with no sessions; batch
  and job modes are allowed (moth-quantum, docs/HARDWARE.md:15 and 18-19,
  READ).
- **The three devices, as seen on three dates:**
  - Logan's instance reached ibm_kingston, ibm_fez and ibm_marrakesh when
    docs/HARDWARE.md was read and measured, on 2026-10-01 (:16-17, READ).
  - All three ran v0's jobs on 2026-10-05 (READ, from v0's records).
  - The account lists the same three, and no others, on 2026-10-14
    (MEASURED by `ibm_dryrun_v0.py --probe`).
- That every Open Plan account reaches the same three, later too, is
  BELIEVED. The standing pre-registration (below) names the devices.

**The unit** is one fixed recipe, "the same thing" every time:
- **the named devices,** three today, in three passes;
- **each pass** runs on each device in turn, in job mode, each job
  awaited before the next is submitted. A pass holds two jobs a device:
  - **a control job:** two PUBs at 2,048 shots. They are the known
    answer, X on {0, 1, 3, 7, 12}, and its complement. Bit order is held,
    and every chain qubit is read prepared in 0 and in 1;
  - **a film job:** three PUBs at 16,384 shots, the law and both
    coherence bases. Law and coherence are read in one job. That they
    share a calibration is BELIEVED;
- **so the devices interleave in submission order:** K M F, K M F, K M F.
  The order as run is shown afterwards by the jobs' created and running
  times, as section 4.4 measured v0's;
- **18 jobs and 479,232 shots;**
- **one shot count per job.** Runtime 0.50.0 warns "Specifying different
  'shots' across pubs is deprecated" (sampler.py:129-136, READ;
  bundle.py:53-56);
- **every option stated,** never defaulted, `rep_delay` included. v0 left
  that to each device, so it is `unknown` there;
- **a bundle frozen per unit,** with each device's chain pinned where the
  device allows. Then the compile can stay EQUAL from unit to unit.
  - That is BELIEVED until a second unit shows it.
  - v0's 28 sheet bundles kept their gate lists within one day (section
    4.4).
- **Quantum-Film's bundle format holds v0's job shapes** (bundle.py's
  PLAN). The kit extends it with the unit's (section 13, P5).

**Complete and interleaved.**
- **`unit-incomplete`:** a unit missing any of its jobs, or with a failed
  or retried job. It enters only the comparisons of devices on which it
  is complete.
- **A pair's pool** takes only units complete on both of its devices, so
  both devices average over the same units.
- **`not-interleaved`:** a unit whose devices did not interleave as run.
  Its differences are the device's-and-its-time's (section 8).

**Its cost:** 180 to 216 QPU-seconds by the three cost models (question
9), each job rounded up to a whole second.
- Anyone on the free tier can run it twice in a window, with at least
  168 s to spare.
- It would fit in the 247 s left after v0, until v0's charges roll off on
  2026-11-02.
  - The instrument computes that as 600 less v0's 353 charged seconds.
  - On 2026-10-14 IBM reported a limit of 600 and 353 consumed; the
    client computes the 247 from those (qiskit_runtime_service.py:1316-1330,
    READ).
  - So IBM's 353 equals the instrument's sum of v0's charges.
- **IBM also counts resource units.** The usage it reported on 2026-10-14
  is MEASURED by `ibm_dryrun_v0.py --probe`, read-only:
  - 353 of 600 seconds, and 5.448 of 10 resource units;
  - so v0 cost 0.0154 units a second. At that ratio one unit's 216 s is
    about 3.3 units, and two units fit both limits;
  - the window rolls. Its period ended at the query, so v0's charges of
    2026-10-05 roll off on 2026-11-02.
- The film job's 49,152 shots are twice v0's largest job, so the cost is
  an extrapolation.
  - IBM's dry run would have estimated it, but no mock backend resolves
    for this account (section 13, M1).
  - So the first real unit measures it.

**Why this size.** The instrument costs fifteen designs. Five bracket the
choice:

| design: shots a PUB | QPU s | units a window | fits in 247 s | Hellinger planning ε, three-way | ⟨X0X1⟩ K−F in one unit: certified difference; beyond readout |
|---|---|---|---|---|---|
| film 12,288; control 2,048 | 144 to 171 | 3 | yes | 0.126 | 0.0225; −0.0017 |
| **film 16,384; control 2,048** | **180 to 216** | **2** | **yes** | **0.114** | **0.0278; +0.0040** |
| film 16,384; control 4,096 | 189 to 225 | 2 | yes | 0.114 | 0.0278; +0.0071 |
| film 24,576; control 2,048 | 243 to 288 | 2 | no | 0.099 | 0.0342; +0.0108 |
| split: law 24,576, coherence 8,192; control 2,048 | 153 to 207 | 2 | yes | 0.099 | 0.0135; −0.0113 |

- **16,384 with 2,048-shot controls.** Of the film designs, this is the
  largest that leaves more than a quarter of the window spare after two
  units, by the highest model, and fits in 247 s.
- **4,096-shot controls** tighten the readout bound for 9 s more.
  - One unit's margin rises from +0.0040 to +0.0071.
  - A few pooled cells below need one to three fewer units.
  - Two units then leave exactly a quarter of the window spare.
- **24,576** would decide the Hellinger {device} test at ε = 0.10 within
  one unit. It leaves 24 s spare in a window, and does not fit in 247 s.
- **The split design** also fits, and also decides that test at 0.10,
  because its law job is larger.
  - It gives up coherence: ⟨X0X1⟩ is no longer certified beyond readout
    in one unit (−0.0113).
  - The film shape is preferred because coherence is the only signal
    against the dephased twin (section 7).

**What one unit can certify.** These are projections, at ε = 0, for the
unit's own family of 84 intervals at α = 0.05.
- **The five-crystal share:** kingston **differs** from marrakesh and
  from fez.
- **⟨X0X1⟩:** kingston **differs** from fez, and still differs once
  readout is allowed for, thinly (+0.0040).
- **Both coherences:** marrakesh differs from fez, but not beyond
  readout.
- **The forbidden share and XEB:** unresolved.
- **The strong form,** projected for the law measures: none clears it.
  - On the five-crystal share, under v0's drift, one unit would need
    77,380 shots a film PUB for kingston against marrakesh. Against fez
    it would need 153,166.
  - Marrakesh against fez never clears it under v0's drift. As shots grow
    without bound, its strong form tends to −0.0227: their difference
    less both drifts.
  - For coherence it is not projected: v0 never measured coherence
    drift.
- **"Beyond readout" is about means.** "Isolated as quantum" needs the
  strong form, less the readout bound (section 8).

**What units add, pooled.** The table gives the fewest units at which
each difference is certified, at ε = 0. These are projections. Each unit
is taken from a different contributor, which makes each look's family the
largest.

| pair | five-crystal share | forbidden share | XEB | ⟨X0X1⟩ (beyond readout) | ⟨Y0Y1⟩ (beyond readout) |
|---|---|---|---|---|---|
| kingston, marrakesh | 1 | 2 | >100 | 6 (>100) | 11 (>100) |
| kingston, fez | 1 | 2 | >100 | 1 (1) | 3 (27) |
| marrakesh, fez | 2 | >100 | >100 | 1 (4) | 1 (5) |

- **XEB:** its per-shot spread is too wide for its small differences, so
  it stays a per-device measure.
- **Cells that stay unresolved at 100 units:**
  - marrakesh against fez on the forbidden share, which differ by 0.0002
    in v0;
  - kingston against marrakesh on either coherence, beyond readout.
- **Time-averaged means.** These pooled verdicts are about time-averaged
  means.
  - Whether the devices differ in every unit is the strong form at unit
    granularity (below). It depends on drift between units, which no
    record has measured.
  - The first units measure that drift, and coherence drift with it: v0
    ran coherence once a device.

**Pooling contributions** extends section 8:
- **A run may span crates:** a set of crates, each with its selector.
  - The pooled shots' target is the shot-weighted mean of all their
    jobs' means, so Hoeffding's KL bound applies unchanged.
  - The target is then a mixture over the units that arrived.
- **Anytime validity.**
  - Pooled verdicts are recomputed whenever a unit arrives.
  - Look k spends α/(k(k+1)), and the spends sum to α. A union bound over
    looks then holds every look's verdicts at once.
  - **A look's family is everything that look computes:**
    - the pooled intervals;
    - the same again, leaving out each contributor in turn;
    - every unit's device means, for the strong form at unit
      granularity.

    At ten units from ten contributors, all complete, that is 579
    intervals. With incomplete units each pair pools its own units, so
    the pooled part counts per pair: up to twice the 39 a computation.
  - **It covers only what the standing pre-registration names, on a pool
    that only grows, in order of arrival.** Not covered:
    - a subset or a comparison chosen after seeing units, such as by
      date;
    - a new measure;
    - a unit withdrawn after pooling. Units are refused at intake,
      before any look;
    - arrival that depends on results. A contributor who withholds a
      unit because of what it showed breaks the guarantee. The standing
      pre-registration asks that every unit run be contributed, refused
      ones included.
  - **Each unit's own family** spends its own α, and its verdicts are
    labelled per unit. They never enter a pooled claim.
- **Granularity.**
  - Within a unit, the strong form compares jobs.
  - Across units it compares unit means: every unit's mean on one device
    against every unit's mean on the other.
  - That excludes units drifting apart. It does not exclude jobs moving
    within a unit, which unit means average away.
- **Readout for a difference.**
  - **The confusion model.** Number the pair's qubits 1 and 2, and give
    each a = p10 − p01 and f = 1 − p01 − p10. Then P' = a_1·a_2 +
    a_1·f_2·⟨z_2⟩ + a_2·f_1·⟨z_1⟩ + f_1·f_2·P. Devices are named A and B
    below.
  - **The offset.** With the measured single-site means m' = a + f·⟨z⟩,
    the offset is a_1·m'_2 + a_2·m'_1 − a_1·a_2. Its bound uses certified
    bounds on |m'|. v0's single-site means reached 0.15, so the cross
    terms are not negligible.
  - **The shrinkage.** Since 0 < f_1·f_2 ≤ 1, readout otherwise only
    shrinks a parity toward 0.
  - **The bound.** Take both true parities certified positive, with A
    reading above B. Then readout can have widened the gap only by
    shrinking B, plus both offsets.
    - That is at most g_B·P_B + o_A + o_B.
    - Here g_B bounds 1 − f_1·f_2 on B, P_B bounds B's true parity, and o
      bounds each device's offset.
  - **Its size and kind.**
    - For ⟨X0X1⟩, kingston against fez, in one unit, the bound is
      0.0238.
    - That is fez's shrinkage, 0.0181, plus both offsets, 0.0058, each
      rounded separately.
    - The shrinkage alone is about half of both devices' together,
      0.0355.
    - It is of kind `conditional`.
  - **Across units.** The projection takes each device's readout as
    constant from unit to unit. A pooled bound that does not assume this
    takes one of two routes:
    - **Linear terms, averaged.**
      - **The shrinkage.** With s = p01 + p10 for each qubit, g = s_1 +
        s_2 − s_1·s_2 is at most s_1 + s_2, which is linear. So the
        pooled controls' average of s_1 + s_2, summed over the pair's
        two qubits, times the largest unit's parity bound, bounds the
        average shrinkage.
      - **The a·m' terms** are linear in a, with m' bounded by the
        largest unit's certified bound.
      - **The a_1·a_2 term** is a product of two quantities that vary by
        unit, so it is not averaged. It takes the average of one |a|
        times the largest unit's other |a|.
    - **Or each device's worst unit.**

    Either route adds per-unit readout and single-site intervals to the
    look's family, beyond the 579 counted above.
  - **Section 6.1's +0.0034** is the same model acting on the law's
    values. Their single-site means are 0, so it has no cross terms.
- **A standing pre-registration,** written once before the first unit,
  fixes the devices, the recipe, the measures, the comparisons and their
  tolerances.
  - Every later unit is then declared before it runs, so no selector it
    names is late. Anything it does not name needs a new version of it,
    declared before the units it covers.
  - Per unit it names the Hellinger {device} test on the three-way class
    at ε = 0.12, which the planning rule supports at 0.114. The crystal
    count would need 0.161.
  - Its date before the units is REPORTED, by its commit and push
    (rule 1). It becomes ANCHORED only if lodged with a holder that dates
    it, such as an archive's deposit record.

**Contributions from anyone:**
- **Anchors.** Only a job's owner can re-fetch it from IBM.
  - So each anchor records who made it.
  - A comparison counts anchors made by anyone but its own author as
    REPORTED. That keeps the kind a
    property of the data (rule 9).
  - An audit record is not a comparison. An auditor who fetches a record
    from its holder holds that anchor (section 9.2).
- **Identity.** A contribution carries a public handle its contributor
  chooses, or `withheld` (rule 3). It never carries the provider's
  account or user identifiers.
- **Leave-one-contributor-out.**
  - Every pooled verdict is recomputed without each contributor in turn,
    inside the look's family.
  - Each `withheld` unit counts as its own contributor.
  - A verdict that flips is labelled as resting on one contributor. At
    small k a flip is mostly a sample-size effect, and the label says so.
- **Refusals.** A unit whose known answers fail is refused at intake, as
  in v0 (control `unit-known-answer`, section 11).
- **The limit.** No one but a unit's owner can expose a fabricated unit
  with fresh identities (section 8). Leaving out each contributor in turn
  bounds its weight. It does not detect it.
- **Logan's own units** run through the same kit as anyone's, from a
  clean checkout at a tagged commit.
  - That is this study's reading of Logan's reason for the hold: "as
    similar to a strangers as possible" (2026-10-14).
  - Pooling treats them like any other unit. The one difference is that
    Logan can verify their anchors.
- **No unit runs before the prototype.** The first real unit waits for
  the functional prototype of section 13, by Logan's word. It is not run
  in pieces.

### 9.2 Federated custody: crates held and audited by many groups

**The aim,** in Logan's words (2026-10-14, verbatim): "One key future
addition is that this system should ideally be designed for federated
custodianship, the end goal being QRO crates are able to be archived and
audited by multiple groups independently. Moth will be approached first to
consider a pilot program and validating the QRO system, followed by
potentially ASU if the format proves decent. One key feature Moth could
bring is repeated runs on their engines once real QPU hardware is used on
them, for example their coin toss engine, collecting every run of that
would enhance the QRO of their coin toss engine for data analysis, the
shared custody will also enable open and easy access to QPU information
where not many sources exist at current".

Everything below is PROPOSED, except where it says READ or BELIEVED.

**Three roles.** One group may hold all three, or each may be a
different group:
- **a producer** runs the jobs and writes the crate: a contributor
  (section 9.1);
- **a custodian** keeps byte copies of crates and their records, and
  serves them;
- **an auditor** runs a checker on a crate and records the verdict.

**What the design already gives a federation:**
- **A crate's identity is its metadata-body digest,** over canonical bytes
  with the header normalised (section 9 and rule 4). Two custodians holding
  the same crate can show it is the same without trusting each other.
- **Every CHECKED field re-derives from the crate alone** (section 10).
  Any auditor with the checker reaches the same verdict.
- **A crate carries no account identifiers** (rule 3), so it can be
  published.
- **Nothing is edited.** A correction is a new crate that supersedes the
  old, as cft-fp256's certificates do with `supersedes`, and custodians
  keep both.

**What it adds:**
- **An audit record,** kept beside the crate it audits and never inside
  it. It holds:
  - the crate's body digest;
  - the checker, and its commit;
  - the verdict: accepted, or the refusal's name;
  - which stages ran: crate-only, and any of section 10's three that need
    more. The anchor re-fetch is among those three, and for IBM's jobs
    only their owner can make it;
  - the auditor's public handle (rule 3), and the date on the auditor's
    clock. Both are REPORTED;
  - its degree of independence (below), REPORTED, since the auditor
    declares it;
  - the head hash of the auditor's own custody log when it wrote the
    record, or `none` if the auditor keeps no log (below);
  - a signature slot and a trusted-time slot, `none` in v0.
- **A custody log for each custodian.**
  - It is append-only and dated. It has one line per event: a crate
    received, with its digest, where it came from, and when; or a crate
    withdrawn (below). Where a crate came from is a public handle or
    `withheld` (rule 3).
  - Each line carries the SHA-256 of the line before it. So an edited or
    dropped line shows at the next line (control `custody-chain`,
    section 11).
  - The last line has no next line. A custodian who edits or drops it,
    or rewrites the log's tail and recomputes its hashes, shows nothing
    in its own log: a stated limit.
  - The first line's predecessor is the SHA-256 of the empty string, so
    dropping the first line shows too.
  - **An audit record carries its auditor's log head hash.** It pins the
    log up to that head on two conditions:
    - the record is held by someone other than the log's writer;
    - the log is shown to a checker.

    Then a later edit, drop or rewrite at or before the head shows. Lines
    after the head stay uncovered.
  - **An empty log, or none at all,** gives the head `none`, which pins
    nothing. A checker cannot tell an honest `none` from a withheld head:
    a stated limit.
  - Each custodian keeps its own; there is no shared ledger to agree on.
- **Disagreement is a finding.**
  - If two auditors' records differ on one crate digest, both stand.
  - The difference names a checker version, a stage, or a fault.
  - A new record resolves it, not a vote.
- **Withdrawal is the one exception to keeping both.**
  - A crate found to carry an identifier rule 3 forbids is withdrawn by
    every custodian that holds it: its bytes are removed.
  - Its custody-log line stays unaltered. A later line records the
    withdrawal and the reason, with no identifier in it (rule 3), and
    the hash chain stays whole (control `withdrawal-appended`, section
    11).
  - A corrected crate supersedes it.
- **Independence has degrees,** and an audit record says which:
  - the producer's own checker build;
  - the same checker source, built independently at a tagged commit;
  - an independent implementation of the checker, written from this
    profile's text.

  None of the three is an external authority in HonestFramework's sense.
  Two implementations on one input is "a real and useful check... It is
  not an external authority" (METHOD.md section 1, READ).
  - The third degree is the strongest check of the checker's code and of
    the profile's text.
  - The external checks stay those of this study's section 10: the
    provider's copies, the known answers, and a second group's own
    records.
- **Provider custodians.** A provider keeps records of the jobs run on
  its platform. Rule 1's test is whether the producer controls the record.
  - **Another producer's job.** For a contributor's job on the provider's
    platform, the provider's records are not the contributor's to
    control. An auditor who fetches them from the provider holds an
    anchor: ANCHORED, with the provider as holder.
  - **The provider's own job.** When the provider is itself the producer,
    as for runs Moth records of its own engines, the records are the
    producer's own. They are REPORTED, with the holder named, until
    signatures (v1) let others check the provider's statement against
    the provider itself.
  - **IBM.** That IBM attests to no one's records but their owner's is
    BELIEVED. For IBM jobs, the anchors stay their owner's (section
    9.1).
  - **Moth's qpu mode.** When a Moth engine runs on IBM hardware through
    Moth's account, Moth is the IBM job's owner and can re-fetch IBM's
    copy. That is BELIEVED, from the engine's description: a blank token
    uses "Moth's own IBM account".
- **Signatures and a trusted time** become necessary once custodians
  attest to one another's crates. v0 names their slots in every audit
  record and on every crate's root, as `none` (sections 9 and 12); v1
  fills them.
- **Open access needs a data licence** that lets any custodian copy and
  serve crates. It is CC BY 4.0, by Logan's word (question 18).

**The pilot sequence.** The order, Moth first and then ASU, is Logan's
plan. What each might do is this study's proposal. Every approach to
another group is Logan's to make.
- **Moth first,** as the first custodian and auditor besides Logan:
  - auditing v0's crates. Among them is the Atlas crate, which holds data
    from Moth's own platform;
  - exposing what future Atlas runs could carry: the compile, and a
    commitment the provider holds.
    - v0's Atlas crate stays "recorded".
    - Its provider never held a commitment, and no seed exists on the
      platform (section 4.3). Those are `none`, which no later record
      supplies;
  - later, crates of every run of its engines on real QPUs, such as its
    coin toss engine.
- **ASU after,** if the format proves decent: an independent academic
  custodian, and perhaps the author of an independent checker.

**The coin toss engine as a QRO question.** Moth's published description
of `coin-toss-v1` is in Quantum-Film's records: the Atlas response of
2026-09-25,
docs/records/2026-09-25/atlas/20260925T173228348516Z_GET_api_v1_engines_coin-toss-v1.json,
READ. Its code is not read.
- **What it does.**
  - "A single qubit is put into equal superposition with a Hadamard gate
    and measured `shots` times."
  - It returns the heads and tails counts, the shots, and which side won.
    It returns no per-shot record.
  - In mode `emu` it runs on the platform's simulator; in mode `qpu` it
    runs on IBM hardware. That is through Moth's account, unless the
    user gives an IBM token of their own.
  - Its built circuit is not exposed: a build-only request returned 410
    twice (docs/VALIDATION.md:63, READ).
- **Its law** is a fair coin's: heads with probability 1/2 exactly. Its
  classical twin is the fair coin, with the same law. So every measure on
  it is integrity (section 7's rule): the heads share of each run, and
  how it moves between runs, devices and dates.
- **So its crates could audit** the engine's bias and drift, run by run
  and device by device, and pool them as section 9.1 pools units.
- **Its outcomes alone could not show that its randomness is quantum.**
  That takes a different experiment, such as a Bell test, which needs
  at least two measured systems (BELIEVED, not read from a source here).
  That lies outside this engine and outside v0's measures.
  - Moth's own description claims no more: "results are a probability
    sample, not a random-number service with guarantees" (READ).
- **Correlations between shots cannot be audited** from counts. Auditing
  them would need per-shot records in the order taken. IBM does not
  document its returned order as that order (section 4.2), and the engine
  returns counts.
- **Its compile is `unexposed`,** as Atlas's is.
- **Its law is exact and simple,** so its crates would be cheap to check.
  Every run repeats the same thing, which is what section 9.1's pooling
  needs.

**What v0 and M1 hold of this:**
- v0 has one custodian, Logan, and no signatures (section 12).
- M1 adds one stage: a second custodian's audit (section 13).
- The rest waits for a partner.

## 10. The authority and the checker

PROPOSED, except where a source is named.

**Two authorities, kept apart.**
- **The physics: the exact law.**
  - A crate carries the law as a table of rationals with its digest.
  - QRO-Crate does not re-derive it from a kernel. It checks the sum,
    the digest and the support, and step 6 holds it to the question's own
    law circuit by simulating that circuit (see section 17).
  - The instruments recompute the 4x4 law from its integer kernel as a
    check: 1,360 forbidden of 4,368, weights {0, 1, 4, 9} × 256, summing
    to 16^5. Draft 2's re-check held them to `compare.exact_law` on all
    4,368 layouts (MEASURED).
- **Everything a crate derives: QRO-Crate's golden model.**
  - That is the decode, the measures, the twins, the floor, the certified
    intervals and the exact hold.
  - It is pure Python on the standard library, independent of
    `quantum_film.compare`, and a test reads its imports to hold that.

**The first external check, and what it is worth.**
- The seam test regenerates moth-quantum's docs/HARDWARE-RESULTS.md
  tables from the crates. Those tables are `quantum_film.compare`'s, from
  the same records. Atlas's ⟨X0X1⟩ there is the engine's derived
  observable, carried as REPORTED.
- Agreement is two implementations of one calculation, which proves the
  parse and the arithmetic. A committed figure is "an external authority
  only if the source derived it from something other than the input you
  are feeding it" (HonestFramework, METHOD.md section 1, READ).
- The external checks on the records themselves are:
  - the provider's copies (section 4.5);
  - the known answers;
  - a second group's records (question 12).

**Beside the checker,** the custody-log check of section 9.2 holds a
custodian's log and its audit records. It refuses with `custody-chain`
or `custody-head`, and accepts a withdrawal written as a later line
(section 11). It is P0's, outside the checker's nine steps (section 13).

**The checker** re-derives everything CHECKED from the crate alone, in
this order. It refuses at the first failure, by name and location
(cft-fp256's strict reader, docs/CERTIFICATES.md:852-899, READ):
1. the bytes (`spelling`, `field-kind`, `term-unknown`);
2. every file against its digest (`raw-digest` and the like);
3. every count against what it counts (`count-unpaid`), and every raw
   result's form (`raw-form`);
4. every commitment, recomputed and held to the one the provider echoed
   (`commitment`; the IBM crate only, since Atlas echoes none);
5. the decode, with bit order held to the known answer (`known-answer`);
6. every measure and declared class (`measure-class`);
7. the exact hold on every gate list (`compile-uncontrolled`);
8. every calibration link (`calibration-link`), and every values-digest;
9. the generated metadata: regenerated, the header normalised, and
   compared byte for byte.

**Three checks that need more than the crate.** Each is a stage that
skips by name without its tools:
- **the compile, re-derived** through the named qiskit. That is
  "a function of the circuit, the target (the day's calibration), the
  seed and the qiskit version" (moth-quantum, docs/HARDWARE.md:109-111,
  READ);
- **each QPY's gate list**, re-derived through qiskit and held to the
  held gate list. bundle.check only hashes the QPY (R12);
- **the anchors**, re-fetched from the provider with the owner's key,
  while it keeps the jobs (section 4.5).

## 11. The controls

PROPOSED.
- Each control is one planted fault, under `controls/`. It must be
  refused by the name given, or stated as the table says.
- Every genuine crate is the set's twin, and must be accepted
  (moth-quantum, README.md:303-307, READ).

| control | planted fault | expected |
|---|---|---|
| shot-moved | one shot changed, its digest left | `raw-digest` |
| job-reattributed | one IBM job's raw result filed under another's id | `commitment`; or `count-unpaid` first, where the two jobs' shot counts differ |
| bits-mirrored | the decode told the mirrored order | `known-answer` |
| compile-broken | a gate-list change that moves a Z-basis probability, digests recomputed | `compile-uncontrolled` |
| qpy-only | one QPY byte changed, with its digest, the commitment, IBM's echo of it inside the raw result and every digest recomputed, the gate list left | accepted by the crate-only checker. Refused by the QPY stage or by the anchor's re-fetch, where the provider's copy differs |
| calibration-late | a snapshot stamped or measured after the first shot, claimed `history-at-first-shot` | `calibration-link` |
| calibration-gap | a job linked `history-at-first-shot` whose first shot falls after a newer carried snapshot's stamp and newest value date | `calibration-link`: the link is `history-in-gap` |
| calibration-restamped | two snapshots with equal values and different stamps | not a refusal: their values-digests are EQUAL |
| count-unpaid | `shots` stated one higher than held | `count-unpaid` |
| self-compare | a run against itself | `comparison-trivial` |
| resealed-compare | a run against a copy with one shot moved and digests recomputed | `comparison-trivial`: the two share job ids and commitments |
| shared-control | two runs sharing only a known-answer job | not refused (section 8) |
| class-declared | a measure declared "signal" with equal law and twin values | `measure-class` |
| float-spelt | a value spelt as a JSON number | `spelling` |
| kind-missing | a field with no kind | `field-kind` |
| adjusted-as-raw | a non-integer corrected count in the raw slot, digest recomputed | `raw-form` |
| single-runs | one law job a run | "not isolated from the pipeline: drift UNMEASURED, `none`" |
| readout-unbounded | runs whose only readout control is one known-answer pattern | "isolated as quantum: no, readout's effect unbounded" |
| time-confounded | runs on two devices in disjoint time blocks | "the difference is the device's-and-its-time's" |
| joint-omission | per-cause tolerance checks that each pass, offered in place of the data | refused: verdicts are computed only on the runs' data |
| shot-moved-resealed | one shot moved, every digest recomputed | accepted by the crate-only checker, a stated limit. Refused by the raw re-fetch, where the provider's copy differs |
| unit-known-answer | a free-tier unit whose known answer fails on one device | refused at intake: `known-answer` |
| unit-incomplete | a unit missing one film job | kept as `unit-incomplete`, and left out of every pair with that device |
| not-interleaved | a unit whose devices ran in blocks | kept as `not-interleaved`: "the difference is the device's-and-its-time's" |
| kit-dirty | the kit started from a tree with uncommitted changes, or from an untagged commit | refused by the kit before any submission: `kit-dirty` |
| simulator-in-real | a `simulator` unit that passes its known answer, offered to a comparison declared real | refused: `kind-not-qpu` |
| custody-chain | a custody-log line edited or dropped after the fact, with a line after it | refused: `custody-chain`, at the first line whose predecessor hash fails |
| withdrawal-in-place | a withdrawal written by editing the crate's received line, with a line after it | refused: `custody-chain`, at the next line |
| withdrawal-appended | a withdrawal written as a later line, with its reason | accepted: the chain stays whole |
| audit-head-mismatch | an audit record whose log head hash matches no line of the auditor's custody log | refused: `custody-head` |

**Three lessons from Quantum-Film** (moth-quantum, CLAUDE.md:88-104 and
isa.py:50-54, READ):
- The same film is never a sabotage: negating every angle and reversing
  the qubit line are gauges. So `bits-mirrored` is held by the
  asymmetric known answer.
- A control named by a number can miss, so every plant is one the checker
  must see bit for bit.
- A change that leaves every Z-basis probability alone passes the exact
  hold, so `compile-broken` plants one that moves a probability. The
  hold's blind spot is stated in section 12.

## 12. What v0 does not do

PROPOSED, as stated limits. Each states the behaviour it concedes.
- **Isolate anything from the pipeline, or as quantum, between its
  devices** (section 6.1):
  - every strong form is unresolved against its drift bounds;
  - the coherence role ran once a device, so its drift is UNMEASURED,
    `none`;
  - the producing commit is `unknown` per job;
  - no readout control covers a measure's qubits in both directions.

  Any difference it could isolate would be the device's-and-its-time's,
  since every job ran in its device's own block.
- **Bind anything beyond the provider's copy.** The re-fetches bind v0's
  submissions and raw results to IBM's copies as of 2026-10-14, and only
  while IBM keeps the jobs. That the device measured what IBM holds is
  beyond any re-fetch.
- **Let anyone check another contributor's anchors.** Only a job's owner
  can re-fetch it (section 9.1).
- **Let anyone else repeat the reads, or re-derive them offline.**
  - The read's records keep each comparison's result, not IBM's gate
    lists or their digests. So the 68 of 68 needs the owner's key to
    repeat.
  - The first read's MANIFEST names moth-quantum's files, not its
    commit. The results MANIFEST names neither. The commit, 3a73823, is
    stated in their README.
- **Show a calibration was in force.** A link is what the history
  returned, a necessary condition. For 8 jobs a newer snapshot was also
  possible (`history-in-gap`).
- **Order events across two clocks** beyond the bounds of section 4.4.
- **See a gate-list change that leaves every Z-basis probability alone**
  (isa.py:50-54). Only the digests refuse it, and only when they are not
  recomputed.
- **Separate device from time,** where runs are not interleaved.
- **Measure drift across days:** v0's IBM data are one day.
- **Adjust anything:** readout correction and mitigation are exploratory,
  beside the measures.
- **Speak for Atlas's compile or sampler,** which are `unexposed`.
- **Take a law that is not rational:** the 16x16 stock would need
  cft-fp256's enclosed values.
- **Cover other providers or modalities, mid-circuit measurement or
  feed-forward.** cft-fp256's certificates cannot yet express streams
  that change per segment (docs/CERTIFICATES.md:3371-3376, READ), and
  this design takes on no more.
- **Sign, or carry a trusted time:** the slots are named, and `none`.
- **Hold a custody log's last line.** An edit, drop or rewrite of a log's
  tail shows nothing in the log itself, until an audit record held by
  someone else pins it (section 9.2).
- **Be held or audited by more than one custodian.** v0 has one
  custodian, Logan. Section 9.2 is the design for more, and M1 tries it
  once (section 13).
- **Have a permanent IRI** (question 6).

## 13. A first round, if this is approved

PROPOSED, under ParcelRound at f42242e (METHOD.md, READ).

**First, the plan goes past its verifier.** ParcelRound keeps "The plan
of record, and a verifier on it before the owner approves it" (METHOD.md
section 7). Drafts 1 to 11 went past verifiers, and draft 12 goes next, on
Sonnet by Logan's word. It did: its re-check found it READY, and Logan
approved it on 2026-10-14.

**The round's target: a functional prototype, M1.** Logan, 2026-10-14:
"Hold off on a real run until we have a functional prototype "crate",
rather than running bits and pieces." So the round ends at a prototype
that does everything a stranger would do, except spend QPU time. It
passes its verifiers in these six stages:
1. **The format.** The vocabulary table, the canonical writer, the
   strict reader and a draft profile: enough to write a crate and check
   it (P0 and P4).
2. **v0 as crates.**
   - The adapter writes v0's IBM campaign, with the 2026-10-14 provider
     records, and v0's Atlas runs, as two crates.
   - With P2's measures and exact hold, the checker accepts both.
   - The checker meets each crate-level control of section 11 as that
     section states it: refused by the name given, or accepted and
     stated. The unit's controls wait for stage 3, and the comparison's
     for stage 4.
   - This shows the format holding real data (P1 and P2).
3. **A unit, run locally.**
   - The contributor kit freezes a free-tier unit and runs it on the
     local fake backends for kingston, marrakesh and fez, which ship with
     runtime 0.50.0. They are FakeKingston, FakeMarrakesh and FakeFez,
     whose property snapshots are dated 2026-04-15, 2025-02-26 and
     2025-02-26 (fake_provider/backends/, READ). So a local unit tests
     the pipeline, not the devices.
   - This is Quantum-Film's own "--dry-run": a local simulator, not IBM's
     server-side dry run (stage 5).
     - Quantum-Film binds a bundle's kind, `qpu` or `simulator`, into
       its commitments, and refuses a backend of the other kind
       (tools/hw_run.py:255-261, READ).
     - So a local unit is its own `simulator` bundle.
   - It writes the crate exactly as for a real unit. The kind is
     `simulator`, and the anchors are `none`.
   - The checker accepts it (P5).
4. **The comparison.** Two local units are pooled in a comparison
   declared a rehearsal.
   - A rehearsal may pool `simulator` units. It says so in its body, and
     is never cited as a result.
   - A comparison declared real admits only `qpu` units (control
     `simulator-in-real`, section 11).
   - The rehearsal's verdicts are computed and re-derived (P3).
5. **A pre-flight against IBM, read-only,** the last check against IBM
   before a real unit. The kit checks the unit's jobs against IBM without submitting
   them:
   - each circuit against the device's current target and its faulty
     qubits and couplers. Runtime 0.50.0 does both client-side before any
     submission (base_primitive.py:155-164, READ);
   - the instance's remaining usage, in seconds and in resource units,
     against the unit's highest-model cost;
   - each job's `max_execution_time`, capped as Quantum-Film's bundles
     cap theirs.

   **IBM's dry run is unavailable to this account,** an inference from
   the lookups (MEASURED) and the refusal path (READ) below.
   - Runtime 0.50.0's `dry_run` "performs a dry run without executing
     the job on a QPU". It can "validate the job, estimate usage
     consumption", and returns "randomized mock data"
     (base_primitive.py:127-142, READ). The same docstring says access
     "may be restricted".
   - Logan cleared dry runs to run anytime (2026-10-14).
   - Before submitting, the runtime renames the backend to its mock
     counterpart, and refuses if no such backend resolves
     (qiskit_runtime_service.py:1102-1111, READ). Its lookup tries the
     account's listing first, then one configuration request by name
     (:1004-1029, READ).
   - Both failed for all three devices (MEASURED, 2026-10-14, read-only,
     by `ibm_dryrun_v0.py --probe`):
     - the account lists ibm_fez, ibm_kingston and ibm_marrakesh, and no
       mock backend;
     - asked by name, IBM answered 404, "device not found", for
       mock_kingston, mock_marrakesh and mock_fez.
   - So no dry run was submitted.
   - The kit keeps a dry-run route for an account whose mock backends
     resolve. Until this one's do, the first real unit is the first
     measurement of IBM's charge for the unit's job shapes.

6. **A second custodian** (section 9.2).
   - The checker is built from a fresh clone at a tagged commit by
     someone other than the producer.
   - It audits byte copies of the crates from stages 2 to 4, and writes
     audit records and a custody log.
   - The custody controls of section 11 are met here: `custody-chain`,
     `withdrawal-in-place`, `withdrawal-appended` and
     `audit-head-mismatch`.
   - Its verdicts and digests must equal the producer's.
   - In M1 a verifier stands in for the second group. That shows the
     mechanics, not independence.

**Then the first real unit, M2.**
- Logan runs it through the same kit, from a clean checkout at a tagged
  commit, as a stranger would.
  - That is this study's reading of Logan's reason: "That also helps keep
    our runs as similar to a strangers as possible" (Logan, 2026-10-14).
- The kit records its own commit in the crate's body, not its header. It
  produced the jobs, so a comparison holds it EQUAL or names it DIFFERS,
  under cause 3.
- It refuses a dirty tree, as Quantum-Film's Atlas runner does
  (tools/pauli_atlas_run.py:150-155, READ).
- It also refuses an untagged commit, which is this design's own rule.
- Control `kit-dirty` holds it to both (section 11).
- It is real QPU work, and so Logan's word.

**The repository's floor**, copied, not invented:
- moth-quantum's verify/run.sh and pytest-stage.sh;
- HonestFramework's check_generated.py pattern;
- moth-quantum's tools/check_docs.py;
- a privacy gate in HonestHarness's tools/check.py style. The re-check ran
  its patterns over this study and found nothing;
- the CLAUDE.md and docs/VALIDATION.md templates;
- `.gitattributes` with `-text` for every hashed file. It is in place:
  `* -text`, since nearly every file here is hashed (question 10).

**P0, the lead's**, landed before any parcel, and past its own verifier:
- the vocabulary table, from which the context, the profile's vocabulary
  and the refusal list are generated, each with a `--check` mode;
- the canonical writer and the strict reader;
- the formats of the audit record and the custody log (section 9.2),
  which the checker writes;
- `verify/run.sh`;
- `controls/` and its two-way registry test.

**The parcels.** Each has a verifier on Sonnet, and runs on Sonnet itself
where its direction is settled. Every brief carries:
- design first, for P1 and P3;
- READY stated before the first pass, as "a gate, or a stated limit";
- its own scratch directory, holding no secret;
- long runs handed back to the lead;
- "anything you found that the brief got wrong", and what it did not do.

The parcels:
- **P1, the adapter:** Quantum-Film's records and the 2026-10-14 provider
  records into crates.
  - Its negative control is `job-reattributed`.
  - Its stated limits are tested by `shot-moved-resealed` and `qpy-only`.
- **P2, the golden measures:** measures, twins, floor, certified
  intervals and the exact hold.
  - Its negative control is `class-declared`.
  - It must show that a twin equal to the law makes every measure
    integrity.
- **P3, the comparison:** runs, selectors, refusals and verdicts.
  - Its negative controls are `self-compare`, `resealed-compare` and
    `joint-omission`.
  - `single-runs`, `readout-unbounded` and `time-confounded` must say
    what section 11 says.
- **P4, the profile:** the Profile Crate at a resolving IRI, the context,
  the shapes and the examples.
- **P5, the contributor kit:** the free-tier unit's runner, built on
  Quantum-Film's, with its anchor re-fetch and the crate writer.
  - With it, anyone on the Open Plan can run a unit and produce a crate
    (section 9.1).
  - It has three routes, and writes the same crate format on each,
    naming Quantum-Film's `kind` and `route`:
    - **local fake backends:** a `simulator` bundle;
    - **IBM's dry run,** where the account's mock backends resolve. Its
      results are mock data, so its known answer fails by design. Its
      crate is kept only as a pre-flight record, and never pooled;
    - **a real run:** a `qpu` bundle.
  - A comparison declared real admits only `qpu` units. A rehearsal may
    pool `simulator` units, says so in its body, and is never cited as a
    result.
  - It takes the key from wherever its user keeps it, never from a
    path of Logan's.
  - It must refuse to submit more than one unit's QPU time, and must
    leave the key and the instance out of every file, as Quantum-Film's
    runner does.
  - Before a real unit, it refuses unless the instance's remaining usage
    covers the unit's highest-model cost, in seconds and in resource
    units (section 9.1).
  - It runs in job mode, each job awaited before the next.
  - It extends Quantum-Film's bundle format, whose PLAN holds v0's job
    shapes, with the unit's.
  - Its controls are `unit-known-answer` and `kit-dirty` (section 11).

**Who owns each checker step** (section 10), and each control:
- P0: the bytes, the digests, the counts, and the regenerated metadata.
  Those are steps 1 to 3 and 9.
  - P0 also owns the custody-log check, outside the crate checker's nine
    steps: `custody-chain`, `custody-head`, and the withdrawal line.
- P1: the commitments, the decode and the calibration links. Those are
  steps 4, 5 and 8.
- P2: the measures and the exact hold, steps 6 and 7.
- P3: the comparison's refusals.
- P5: the kit's refusals.
- A control belongs to the parcel whose step refuses it, or states it.

**The seam tests, the lead's:**
1. regenerate moth-quantum's docs/HARDWARE-RESULTS.md tables, and every
   figure of section 6.1, from the crates;
2. compare the three devices as selections of one crate, and read the
   statuses and verdicts against (1).

**The ledger** sits outside every worktree, as `qro-crate-ledger`, with
one file per author and an escalation rule. It is archived and kept at
the round's end. Every lead commit, merge and record entry goes past a
verifier before main moves.

## 14. Questions for Logan, with recommendations

**Decided, 2026-10-14:**
- **The plan of record:** Logan approved draft 12 (`f8a983e9…`), with
  every recommendation below as written, and the confirmation list.
  Question 13, which has no recommendation, and question 16's agreement
  tolerances stay open.
- **1. What "the quantum difference" means:** (c), both layers.
- **4. Key use:** approved, and widened the same day to any use but real
  QPU work. Both reads are done (section 4.5).
- **11. The adopted standard:** Kourousias et al.'s, in the semantic form
  for bounded means and the Hellinger form for declared laws (section 8).
- **18. The crates' data licence:** CC BY 4.0.
- **10, in part: the licences and `git init`.** The code is MIT, as
  HonestFramework, ParcelRound and Quantum-Film use (their LICENSE files,
  READ). The documents are CC BY 4.0, with the data.
  - Creative Commons advises against its licences for software: "We
    recommend against using Creative Commons licenses for software" (its
    FAQ, READ by draft 8's re-check). So the split is deliberate.
  - Logan's first words left a condition: "unless it would be simpler
    to keep both CC BY 4.0". The lead advised it would not be, and Logan
    confirmed MIT the same day.
  - **The repository was initialized on 2026-10-14,** on branch `main`.
    - `LICENSE` holds the MIT text and `LICENSE-docs.md` the CC BY 4.0
      grant, as a link to the licence. "A link is fine rather than full
      legal text as well" (Logan, 2026-10-14).
    - `.gitattributes` sets `* -text`, so git converts no line endings.
    - A scratch copy of draft 11's tree, committed and cloned with
      `core.autocrlf=true`, kept all 164 files byte for byte, its 8 CRLF
      files among them. MEASURED by the lead with git 2.45.2 and a byte
      comparison, and again by draft 11's re-check. Without
      `.gitattributes`, the re-check's same trial changed 155 of 163
      files, every LF one.
    - Draft 12's re-check repeated it on draft 12's tree: all 165 files
      kept, 8 CRLF among them, and 156 of 164 changed without the
      attribute.
    - Nothing is committed yet.
  - Each crate names its own licence in its metadata, on the root data
    entity, so the split needs no guessing.
  - Quantum-Film's own files are Logan's, under MIT (its LICENSE, READ).
    The adapter records that beside each one, as provenance.
  - Some copied files hold providers' text and data: Moth's Atlas
    responses, and IBM's job records. Their terms are not examined here.
    That publishing them under the crates' licence is permitted is
    BELIEVED, and is for Logan to check before the repository is public.
  - The public repository is still open (question 10).

**Open until the approval, with the recommendations it adopted:**
2. **Two named twins, classes computed from them,** and "isolated as
   quantum" naming its twin. *Recommended: yes.* (Section 7.)
3. **The seven causes and four statuses, one per cause per measure,**
   with what both runs share listed as unseen. CONTROLLED means a
   certified bound on the effect exists. *Recommended: as section 6 has
   it.*
5. **The records are the source of truth,** and the metadata is generated
   from them. *Recommended: yes.* (Rules 4 and 5.)
6. **The profile's identity.** A provisional IRI now, on a page that
   resolves, as RO-Crate requires; w3id.org at v1 is a public pull
   request and Logan's to make. *Recommended: yes.*
7. **Quantum-Film as a submodule at 3a73823,** every copy held to it by
   digest. *Recommended: yes.* (Section 9.)
8. **The levels:** recorded, anchored, comparable, quantum-comparable.
   *Recommended: yes.* (Section 9.)
9. **The next hardware round: the free-tier unit of section 9.1,** run
   by Logan and by anyone on IBM's Open Plan.
   - **Decided, 2026-10-14:**
     - no real run until a functional prototype crate exists (section
       13). Each real run remains Logan's word;
     - dry runs are cleared anytime.
   - **MEASURED, 2026-10-14:** no mock backend resolves for this
     account, by listing or by name.
   - **READ:** the runtime's dry run needs one, and refuses before
     submitting without it.
   - **So,** by inference from both: IBM's dry run is unavailable to this
     account. None was tried (section 13).
   - **Proposed, as this study's reading of Logan's reason:** Logan's
     units then run through the same kit as a stranger's.
   - **Its shape:**
     - the devices the standing pre-registration names, three today, in
       three interleaved passes;
     - each pass a control job (2 × 2,048 shots) and a film job
       (3 × 16,384) on each device;
     - 18 jobs and 479,232 shots.
   - **Its cost:** 180 to 216 QPU-seconds.
     - That is two units in any 28-day window. The Open Plan gives "10
       QPU-minutes per rolling 28 days" (moth-quantum,
       docs/HARDWARE.md:15, READ).
     - One unit fits in the 247 s left after v0 (docs/VALIDATION.md:1701,
       READ).
   - **The cost models,** each an estimate, with every job rounded up to
     a whole second:
     - IBM's charge for v0's law jobs, 9 s per 24,576 shots, scaled
       through the origin;
     - a least-squares line through all 65 of v0's jobs;
     - Quantum-Film's own "about 2 s plus about 0.35 ms a shot"
       (docs/HARDWARE.md:28-29, READ).
   - **The roles it carries:**
     - every role, coherence included, three times a device;
     - devices interleaved by construction;
     - readout controls in both directions in the job before every film
       job.
     - qiskit-ibm-runtime 0.50.0 deprecates different shot counts across
       a job's PUBs (bundle.py:53-56), hence the separate control job.
       Kourousias et al. ran 256-shot controls inside each job, on
       0.47.0.
   - **Also carried by every unit:**
     - `job.properties()` and the history at the first shot, read at run
       time, and read again past the history's lag (section 4.5);
     - **a calibration id, requested.** Runtime 0.50.0 sends one "to use
       with the program execution" (api/rest/runtime.py:95 and 122-123,
       READ). Whether IBM's records then name it is to be recorded
       (section 3);
     - the provider's copies kept as digests, not only as the results of
       comparing them (section 12);
     - every option stated, `rep_delay` included;
     - a measured clock offset;
     - the producing commit in every record. Quantum-Film's Atlas lines
       already carry `code_commit`.
   - **Larger shot counts** for the paper's Hellinger test, and their
     cost, are in section 16.5. At ε = 0.05 a nine-job campaign needs 17
     to 21 QPU-minutes on the three-way class alone.

   *Recommended: the unit as section 9.1 has it.*
10. **The public repository.** The licences and `git init` are decided
    and done (above). What remains:
    - a public GitHub repository at the first round;
    - before that, Logan checks the providers' terms for the text and
      data its records copy (above).

    *Recommended: both.*
12. **Kourousias et al.'s archive as a second corpus.** CC-BY-4.0 "unless
    defined otherwise", about 20 MB. It holds raw ibm_kingston outcomes of
    2026-09-29. *Recommended: yes, after v0's own crates.*
13. **Whether to write to the authors.** *No recommendation:* this is
    outward-facing.
14. **The correction to Quantum-Film's docs/HARDWARE-RESULTS.md:194**
    (section 4.5).
    - For the morning run, the reported values did not change.
    - Kingston did recalibrate later: its sheets ran under 342 or 680
      changed values.
    - It would be a new dated entry in Quantum-Film's docs/VALIDATION.md.

    *Recommended: yes, as Logan's or a Quantum-Film round's, not this
    repository's.*
15. **Contributions from others** (section 9.1).
    - A contributor's anchors are REPORTED in every comparison except one
      the contributor wrote (section 9.1).
    - A contribution carries a public handle its contributor chooses, or
      `withheld`.
    - Every pooled verdict is recomputed without each contributor in
      turn.

    *Recommended: yes.*
16. **The standing pre-registration's tolerances** (section 9.1).
    - ε = 0 for "differ".
    - The Hellinger {device} test on the three-way class at ε = 0.12 per
      unit.
    - Agreement tolerances per measure, set before the first unit.

    *Recommended: the first two. No recommendation on the agreement
    tolerances:* they are a scientific choice.
17. **Federated custody as section 9.2 has it.**
    - Audit records sit beside crates, never in them.
    - Each custodian keeps its own custody log. Its lines are
      hash-chained, a withdrawal is a later line, and an audit record
      carries the log's head hash.
    - Disagreement between auditors is a finding.
    - Each audit names its degree of independence.
    - A provider's records anchor other producers' runs on its platform,
      for an auditor who fetches them from it. Its own runs stay REPORTED
      until signatures exist.
    - Signatures come in v1.

    *Recommended: yes.*
18. **The crates' data licence.** Decided, 2026-10-14: CC BY 4.0 (above).
    It keeps attribution, as Kourousias et al.'s archive does, and lets
    any custodian copy and serve crates.
19. **What a Moth pilot would ask of Moth** (section 9.2), in rising
    order of cost to Moth:
    - an audit of v0's crates with the checker;
    - for future Atlas runs, the compile and a commitment the provider
      holds. v0's Atlas crate stays "recorded";
    - custody of every run of its engines on real QPUs.

    *Recommended: that order. Approaching Moth, and later ASU, is Logan's
    to do.*

**Decisions the body takes, for confirmation** (R3), confirmed by the
approval on 2026-10-14. For each, *recommended: as the body has it*:
- a crate is one contribution, a campaign is what one pre-registration
  fixes, and a comparison pools crates (sections 8, 9 and 9.1);
- QRO-Crate holds the law as data (section 10);
- canonical bytes, and the header and body split (section 9 and rule 4);
- the base, RO-Crate 1.3 with Process Run Crate 0.6 (section 9);
- the kinds, including ANCHORED by re-fetch, and `unexposed` (rules 1 and
  2);
- rules 3 and 6 to 9;
- the calibration link's vocabulary, including `history-at-first-shot`
  and `history-in-gap`; the values-digest; and the clock rule (section
  6);
- drift as U(D), with the SD as an estimate, and the floor of three
  repeats (sections 6, 8 and 9);
- the kind `certified` (section 7);
- Hoeffding's KL form, a union-bound family, and the strong form
  (section 8);
- the time block named with the device where runs are not interleaved
  (section 8);
- the refusals and their order (sections 8 and 10);
- the controls (section 11);
- validation in two layers (section 9);
- M1's six stages, as this study's reading of "a functional prototype"
  (section 13);
- the controls `kit-dirty`, `simulator-in-real`, `custody-chain`,
  `withdrawal-in-place`, `withdrawal-appended` and `audit-head-mismatch`
  (section 11), and the refusal `kind-not-qpu` (section 8);
- nothing on the licences: Logan confirmed MIT for code and CC BY 4.0 for
  documents (question 10).

## 15. Sources

**Local, READ on 2026-10-14:**
- **HonestFramework** at 65447fd: README.md and METHOD.md.
- **ParcelRound:** METHOD.md at f42242e and at 8767e23.
- **HonestHarness:** tools/check.py, through the conventions survey.
- **cft-fp256** at f22e8d2:
  - CLAUDE.md and README.md;
  - docs/CERTIFICATES.md, in part by the lead and in full by a survey
    agent;
  - docs/studies/CERT-V2.md and docs/studies/ACC-A-estimates.md, in part.
- **moth-quantum** at 3a73823:
  - README.md and CLAUDE.md;
  - docs/DETERMINISM.md, HARDWARE.md, PREREGISTRATION.md,
    HARDWARE-RESULTS.md and STOCKS.md;
  - compare.py:60-155, 255-310 and 340-361; isa.py:31-54.
- **qiskit-ibm-runtime 0.50.0**, as installed in the qf-ibm virtualenv:
  base_runtime_job.py, ibm_backend.py, utils/converters.py,
  base_primitive.py:127-208, the `calibration_id` and `dry_run` lines of
  qiskit_runtime_service.py, api/rest/runtime.py:79, 95 and 122-123, and
  the names, and the property files' `last_update_date`, under
  fake_provider/backends/.
- **The verifiers' reports:** draft 1's, the re-checks of drafts 2
  to 11, and draft 12's re-check. Draft 4's re-check was delivered in session. The lead transcribed
  its findings into draft 5's verifier packet, and draft 5's verifier
  found the transcription faithful. All twelve are kept in this
  repository's docs/reviews/QRO-0/, whose README states every change made
  to them.
- **qiskit-ibm-runtime 0.50.0's sampler.py:125-140,** for the per-PUB
  shot rule.

**Instruments**, in docs/studies/qro0/, each run with `python -I`.
- Except the three IBM tools and the two checks of this study's text,
  `check_study.py` and `check_study_plants.py`, each refuses unless
  moth-quantum is a clean 3a73823.
- `calibration_at_execution_v0.py` also refuses unless the 2026-10-14
  read's MANIFEST, and every file it lists, hash as recorded, and the
  read's directory holds no file the MANIFEST does not list.

| instrument | SHA-256 | output | output SHA-256 |
|---|---|---|---|
| `sufficiency_v0.py` | `4eacfdd8…` | `sufficiency_v0.out.txt` | `61be0a65…` |
| `v0_timing_and_drift.py` | `dfff4232…` | `v0_timing_and_drift.out.txt` | `3a383646…` |
| `isolation_v0.py` | `3f63f1ae…` | `isolation_v0.out.txt` | `c6f042d2…` |
| `calibration_at_execution_v0.py` | `f1664e57…` | `calibration_at_execution_v0.out.txt` | `89ac4b86…` |
| `free_tier_unit_v0.py` | `1894ef92…` | `free_tier_unit_v0.out.txt` | `a0d3f532…` |
| `ibm_refetch_v0.py` | `aeed00ca…` | records/2026-10-14/ibm-refetch/, `MANIFEST.json` | `1761adbb…` |
| `ibm_results_refetch_v0.py` | `f1187989…` | records/2026-10-14/ibm-results-refetch/, `MANIFEST.json` | `59ac54a2…` |
| `ibm_dryrun_v0.py` | `6ca8b5ae…` (the probes ran `84a7d2d6…` and `ef6aafa3…`) | records/2026-10-14/ibm-dryrun-probe/ and ibm-dryrun-probe-2/, each `probe.json` (`--probe` only: nothing submitted) | `8a721e8d…`, `4d5510e0…` |
| `check_study.py` | `660d7890…` | none: it prints a count line, then ACCEPTED, or REFUSED with each failure and exit 1 | — |
| `check_study_plants.py` | `282ddee1…` | none: it prints each plant's result and the counts, then ACCEPTED, or REFUSED and exit 1 | — |

The three IBM tools run under the qf-ibm virtualenv, with Logan's key.
**`check_study.py` is the study's own gate.** The lead runs it before
every freeze, and each verifier re-runs it. It refuses, naming each
failure, unless four things hold:
- **Draft numbers.** The header's draft number agrees with six
  sentences, each found in its own place:
  - two in the header;
  - section 13's "goes next";
  - section 15's "re-checks of drafts";
  - two labels in section 17.

  Across the header and sections 13 and 15, every copy of the first
  four, in this wording, must name it, in whichever of the three it
  stands. Section 17 keeps each draft's labels, so there the current one
  need only be present.
- **Tables.** Every line that starts with a pipe, after any indent,
  belongs to a table: a run of such lines whose second line is a
  delimiter row. In each table, every row starts and ends with an
  unescaped pipe and has as many cells as the header row, and every
  delimiter cell is three or more hyphens, with optional colons.
- **Section references.** Every section number it reads names one of
  this study's headings. It reads them:
  - after "section" or "sections", in any case and across line breaks:
    a number alone, or a list or range joined by commas, "and", "or",
    "to", a slash, a hyphen or an en dash;
  - as bare numbers in the "where" column of section 17's tables,
    between commas, "and" or ", and".

  It skips a reference just after a file name ending ".md", such as
  "METHOD.md section 7", as another document's.
- **Instruments.** This section's table has exactly one row for each
  `.py` file in docs/studies/qro0/, none for any other `.py` file, and
  each row parses. Each row names the SHA-256 prefix of its file. A row
  whose output cell names a `.out.txt` file names it alone, and that
  file's prefix in the next cell. docs/studies/qro0/ holds nothing but
  those `.py` and `.out.txt` files.

**It checks nothing else.** Among what that leaves unchecked:
- prose and figures. It re-runs no instrument, so a matching output hash
  shows only that the file is unchanged;
- the header's date;
- draft numbers outside those six sentences, including a stale copy of
  one in other wording, or outside the header and sections 13 and 15,
  such as a quotation in section 17;
- the earlier drafts' hashes, the tools' earlier versions' hashes, and
  the records' hashes;
- which row names which output: two rows that swap their outputs and
  output hashes pass;
- a table whose lines do not start with a pipe, such as one in a
  blockquote, and a row that does not;
- a section cited in another form, such as a bare number outside
  section 17's "where" columns, and one cited just after a ".md" name,
  which it skips even if it means this study's;
- whether a cited section is the right one;
- question, rule, stage, refusal or cause numbers;
- the Contents list against the headings, and duplicate headings;
- its own printed counts, which it compares with nothing.

It checks its own hash, so it cannot vouch for itself. It fails closed,
naming what it read: where a section number is followed by a comma and
a date, it reads the date's year as a section too. The lead rewords
such forms.

**`check_study_plants.py` tests the gate.** It plants faults in LF
copies of the study and in copies of docs/studies/qro0/, in a temporary
directory, and runs the gate on each copy, with a time limit. It
refuses unless every plant is placed, every fault is refused with the
failure it targets, and every right variant is accepted. Its docstring
lists the plants: at least one for each check above, and six right
variants. The lead runs it with the gate.

The instruments run without `-O`, so their assertions stay part of their
checks.
`free_tier_unit_v0.py` sizes the free-tier unit (section 9.1). The
outputs are written by Python on Windows, with CRLF line ends, and
their hashes are of those bytes.

**Public, read on 2026-10-14:**
- RO-Crate 1.3.0's release, and the profiles page;
- the Workflow Run RO-Crate 0.6.0 release, Process Run Crate 0.6, and
  the workflow-run context;
- rocrate-validator 0.12.2;
- QProv's user guide (search) and QC-MM (search);
- arXiv:2608.08272 (HTML, downloaded) and arXiv:2608.05041 (abstract);
- arXiv:2610.09931v2: its TeX source, PDF and supplement, downloaded,
  and its archive's page;
- IBM's ExecutionSpan class reference (page) and runtime-job-v2 page
  (search).

## 16. Kourousias et al., "Sufficient quantum provenance"

**What was read.** READ from arXiv:2610.09931v2 (v1 2026-10-07, v2
2026-10-08; CC BY 4.0), downloaded 2026-10-14:
- the TeX source tarball, SHA-256 `d4c3ce3e…`;
- the PDF, `59fb7293…`;
- the supplement, `3d8a20cf…`.

The authors are at Elettra Sincrotrone Trieste, the University of Trieste
and NCSR "Demokritos". Logan adopted its standard on 2026-10-14.

### 16.1 What it is

**Definitions** (its section II):
- **the setting:** fields F; a declared set Ω of complete contexts; each
  context's raw single-shot outcome law p_z;
- **a record** retaining S ⊆ F is the projection, and contexts sharing it
  form a cell;
- **the risk** R_Ω(S) is the largest Hellinger distance within a cell. S
  is ε-sufficient when R_Ω(S) ≤ ε;
- matching records guarantee agreement within ε, while non-matching
  records "do not establish disagreement".

**Results:**
- **A separation certificate** (Proposition 2): minimum-cost retention is
  a hitting-set problem.
- **Thresholds can fail to compose.** Independent full-tolerance
  thresholding of single fields can fail to compose. On its QAOA-1 study,
  omitting routing alone leaves 0.0417 and angle bias alone 0.0497, but
  both together 0.0514, over ε = 0.05.
  - The paper scopes this as "a failure of independent full-tolerance
    thresholding, not of every single-field method".
  - It gives a valid summed bound on a Cartesian context set (S1.4).
- **A channel certificate** (Proposition 1) bounds the law distance
  across a bin of continuous fields, assuming independent stochastic
  noise flags and Pauli-rotation coherent differences.
- **Transcript tensorization** ties precision to a future comparison's
  length. Any hidden discrepancy is eventually detectable, so a tolerance
  belongs to a stated comparison (S1.7).
- **A finite-shot rule:** radii η = √(1 − exp(−c/n)), with c = (B − 1)
  ln 2 + ln(M/α), give pass, fail or unresolved. This is conditional on
  independent, stationary shots within each context.
- **A semantic form** (S1.6) replaces the Hellinger distance with a
  bounded observable's mean difference, in its own units. Section 8 uses
  it.

**Its hardware test** (section VII and S4):
- ibm_kingston, 2026-09-29, three jobs;
- each job holds both six-qubit layouts at 32,768 shots, and asymmetric
  controls at 256 shots;
- Qiskit 2.5.2, level 1, seed 271828, Runtime 0.47.0; dynamical
  decoupling and twirling off; no mitigation; ε = 0.15;
- raw laws need layout retained; decoded laws need nothing;
- of its within-job checks, it says "These descriptive checks are neither
  physical time bins nor tests proving IID sampling."

**Its archive:** Enodo, doi:10.34965/enodo.i61153, about 20 MB in 341
files. Its page says "CC-BY-4.0 unless defined otherwise", and gives
2026-10-06 as the upload date. The archive was not opened.

### 16.2 Where it agrees with this study

READ:
- **raw laws are the comparison object,** and mitigation needs its own
  target (S1.6). Here: rule 6;
- **missing fields are represented explicitly** (S4). Here: rule 2;
- **calibration quantities are contextual metadata** (S4). Here: cause 6;
- **returned order is not chronology** (section VII). Here: section 4.2;
- **confounded factors are reported, not interpreted** (S5). Here:
  section 8;
- **readout controls with every job.** The paper puts them inside each
  job. The free-tier unit puts them in the job just before each film job,
  because runtime 0.50.0 deprecates different shot counts within a job
  (section 9.1);
- **the tolerance and sample size are fixed before the shots.** Here: the
  pre-registration.

Its section I, "From preservation to a guarantee", is READ:
- it lists PROV, research-object packaging, QProv, QC-MM and Qiskit
  compiler tracking as means of collecting and exchanging provenance.
  For packaging it cites Soiland-Reyes et al., 2022, the RO-Crate paper;
- it says preservation alone "does not specify what agreement a second
  execution should achieve".

That an RO-Crate profile is where such agreement can be stated is this
study's inference, not the paper's.

### 16.3 What it changed here

- **The verdict form** (adopted): differ, agree or unresolved, at a
  declared tolerance and confidence (section 8).
- **The semantic form,** for the measures of section 7 (section 8).
- **A slot for a statistical claim:** the kind `certified` (section 7).
  cft-fp256's three kinds (measurement, estimate, bound) have none. That
  was this study's cft-fp256 survey's finding, not a sentence in
  CERT-V2.md.
- **Alphabet size as a cost.** At 24,576 shots and M = 31, the paper's
  radius is:
  - 0.918 for the raw 16-bit law;
  - 0.341 for the five-crystal layout law, with one outcome for "not
    five";
  - 0.027 for the crystal count;
  - 0.018 for the three-way class.

  Only the last two decide anything at v0's counts: the {device} record
  passes at ε = 0.10, and nothing resolves at ε = 0.05 (section 16.5).
- **Composition:** the comparison never certifies from per-cause
  tolerances (section 8).
- **Continuous precision (v1):** Proposition 1 as a `conditional` bound.
  Quantum-Film's devices were worse than their noise models (moth-quantum,
  docs/HARDWARE-RESULTS.md:53), so on hardware it is never CHECKED.

### 16.4 What this study adds that it lacks

- **Attribution and the twins** (sections 6 to 8).
- **Evidence that the prespecification came first.**
  - The paper and supplement describe no commit, hash, timestamp or
    provider-held commitment establishing that order.
  - The archive, unopened, holds job identifiers and provider spans, per
    the paper.
  - HonestFramework's lesson, blinding as "a property of the record"
    (METHOD.md section 9), and Quantum-Film's commitments are the
    mechanism here.
- **Exact arithmetic.** The paper's finite-class laws are "exact channel
  propagation evaluated in floating point" (its section V).
- **Drift.** It assumes stationarity and names a test under measured
  drift as future work. v0's repeats measure drift.

### 16.5 Its Hellinger test, run on v0's data

MEASURED by `sufficiency_v0.py`. M = 31 laws and α = 0.05, per outcome
object, not family-wise over the two objects. Conditional on independent,
stationary shots within each job.

| object | radius | within a device, largest H (kingston / marrakesh / fez) | between devices | record {}: interval; verdict at 0.02 / 0.05 / 0.10 | record {device}: interval; verdict at 0.02 / 0.05 / 0.10 |
|---|---|---|---|---|---|
| crystal count (B = 17) | 0.0267 | 0.0242 / 0.0346 / 0.0236 | 0.0182 to 0.0796 | [0.0263, 0.1330]: fail / unresolved / unresolved | [0, 0.0880]: unresolved / unresolved / pass |
| three-way class (B = 3) | 0.0178 | 0.0211 / 0.0335 / 0.0221 | 0.0003 to 0.0804 | [0.0447, 0.1161]: fail / unresolved / unresolved | [0, 0.0691]: unresolved / unresolved / pass |

**What it says:**
- At ε = 0.10, the record {device} is certified sufficient for the 31
  observed jobs: given the device, the job may be dropped. That holds at
  95% for each object, under the sampling assumption above, and says
  nothing about jobs not run.
- At ε = 0.05, nothing resolves.
- The aggregate is driven by marrakesh. For kingston against fez on the
  crystal count, distances across devices (0.0275 to 0.0648) clear those
  within either device (at most 0.0242 and 0.0236). These are the
  re-check's figures.

**Shots per job for the {device} record.** These take the observed
within-device risk R: 0.0346 on the crystal count, 0.0335 on the
three-way class. Each figure is the least whole count that meets its
rule, for v0's family of 31 laws.

| rule | ε | crystal count | three-way class |
|---|---|---|---|
| the observed-risk test, the paper's Eq. 13, with R as the empirical risk | 0.05 | 294,580 | 114,239 |
| the same | 0.10 | 16,365 | 7,057 |
| the planning rule for a new run, 4η ≤ ε − R, with R as the true risk | 0.05 | 1,178,344 | 456,967 |
| the same | 0.10 | 65,483 | 28,239 |
| the planning rule at zero true risk, 4η ≤ ε: its floor | 0.05 | 112,120 | 50,019 |
| the same | 0.10 | 28,024 | 12,502 |

**For a campaign of nine law jobs (M = 9),** the planning rule asks less:
- on the three-way class, 384,659 shots a job at ε = 0.05, and 23,771 at
  ε = 0.10;
- on the crystal count, 1,095,163 and 60,861.

**What these would cost.** By the three cost models of question 9, a
nine-job campaign at the M = 9 counts costs (`sufficiency_v0.out.txt`):

| object | ε = 0.05 | ε = 0.10 |
|---|---|---|
| three-way class | 17.4 to 21.1 QPU-minutes | 1.3 to 1.5 |
| crystal count | 49.1 to 60.2 | 3.0 to 3.5 |

Section 9.1 sizes the free-tier unit with the same models.

## 17. Send-backs: what each draft changed for its verifier

**Draft 1's verifier** (D1 to D14, answered in draft 2):
- runs became a crate plus a selector (D1, D6);
- CONTROLLED became a bound on the effect, with two layered statements
  (D2);
- the server's settings moved to the device's state (D3);
- the seeded Aer control was replaced by the exact hold (D4);
- the classes moved to count-free expected values (D5);
- the clock bound was corrected for git's truncation (D7);
- ANCHORED came to need a re-fetch (D8);
- the checker gained steps (D9), and the header and body split (D10);
- the questions were completed (D11);
- the survey's labels were fixed (D12), and compare.py's floats stated
  (D13);
- six small fixes (D14).

**Draft 2's re-check** (R1 to R12, answered in draft 3):

| finding | what draft 3 changed | where |
|---|---|---|
| R1: a lower bound rounded up, 0.94 | 0.93 | 4.4 |
| R2: a quotation not verbatim | the supplement's sentence quoted whole | 16.1 |
| R3: section 14 still claimed every decision | the confirmation group now lists the rules, calibration vocabulary, clock rule, drift statistic, refusals and controls | 14 |
| R4: the levels contradicted themselves | a ladder of what a crate carries, with verdicts separate. v0's IBM crate is anchored and not comparable | 9 |
| R5: drift was CONTROLLED by repeats, which estimate spread and bound nothing | drift is CONTROLLED only by a certified U(D), in the strong form | 6, 8 |
| R6: a differing compile was CONTROLLED by a noiseless hold | DIFFERS, logically equivalent. The noisy realization is the device's | 6, 6.1 |
| R7: device confounded with time block | the time block is part of cause 6; interleaving is required to separate it; control `time-confounded`; 6.1 says so | 0, 2, 4.4, 6, 6.1, 8, 9, 11, 12 |
| R8: the headline still overclaimed | "aims to make", and names what it cannot | 0, 1 |
| R9: an absence claim READ from an abstract | BELIEVED for the three works read in part | 3 |
| R10: summaries over-scoped the composition result | scoped as the paper scopes it | 8, 16 |
| R11: the NN correlation called unbiased | approximately unbiased, with the re-check's bias figures | 7 |
| R12: the hold covers gate lists, not QPY bytes | stated; a QPY stage and control `qpy-only`; IBM's copies close it for v0 | 4.2, 4.5, 10, 11 |

**The re-check's notes, taken:**
- on the comparison:
  - the twin named in "as quantum", and readout CONTROLLED marked
    `conditional`;
  - fabricated runs listed among what a comparison cannot see;
  - shared controls allowed by `comparison-trivial`;
  - the selector rule (`selector-late`), and the selector among what a
    comparison does not prove;
  - the floor of three's two degrees of freedom (section 6);
- on the paper:
  - the licence qualifier, and the unopened archive;
  - the paper's own words for non-matching records;
  - its section I quoted, with this study's inference marked;
  - the "no slot" finding attributed to this study's certificate
    survey, not to CERT-V2.md;
  - 16.3's alphabet sizes squared with 16.5's verdicts;
  - the planning figures under both rules, with the zero-risk
    criterion stated;
  - α per object, and "certified sufficient" scoped to the observed
    jobs;
  - the kingston-against-fez separation;
- on v0's figures:
  - the equal-weight and df-weighted SDs;
  - the drift contrast by class, and SD/SE ranges that included
    marrakesh, removed: drift is stated as U(D);
  - the provenance of 6.1's figures;
  - the readout inputs' ages;
- on Quantum-Film and the providers:
  - Atlas returning more than counts, and how its decode was inferred;
  - "commit-before-read order" for git's role;
  - public repository URLs carried under rule 3, which now names the
    provider's identifiers;
  - `job-reattributed`'s shot-count case;
  - the PUB-shots deprecation;
- on the survey:
  - Peltonen's "long-term ecosystem use";
  - the 1.3 profiles page;
  - "between two crates", left from draft 1, now "between two runs".

**New in draft 3, beyond the findings.** These were for draft 3's
verifier:
- **the two IBM reads,** and what they establish (section 4.5);
- **the calibration-link vocabulary,** revised by those reads: a
  values-digest, and `before-first-shot`, renamed in draft 4 (V1)
  (section 6);
- **the adopted standard,** as section 8 now states it, and 6.1's
  certified verdicts;
- **6.1's declaration:** ε = 0, exploratory under `selector-late`;
- **one status per cause,** made per measure in draft 4 (V3), held to:
  - the sampling is CONTROLLED by the inequality;
  - bit order is a precondition, not a status;
  - the device's state and time is one DIFFERS;
- **the time block,** made consistent. A time-block confound qualifies
  "isolated from the pipeline" as the device's-and-its-time's; drift
  is what stops it;
- **the predictions' snapshots,** now compared with those in force by
  the calibration instrument (section 4.5);
- **the QPU-charge estimate,** and the ε = 0.10 planning figures
  (question 9 and section 16.5);
- **question 14,** the correction to Quantum-Film's results document.

**The instruments, in draft 3:**
- "held to HARDWARE-RESULTS.md" is now an assertion that can fail;
- every instrument but the IBM tools pins moth-quantum to a clean
  3a73823;
- the planning lines print three figures at ε = 0.05 and 0.10, each
  inverted exactly, with their QPU charge:
  - the observed-risk test;
  - the planning rule;
  - the planning rule's zero-risk floor;
- the readout model is unchanged when every p01 is swapped with its
  p10, since a_a·a_b and f_a·f_b are both invariant.
  - So no plant of that swap can fail.
  - That is a stated limit of the instrument's check, not of a crate.

**Draft 3's re-check** (V1 to V8, answered here). It found the IBM reads,
the certified intervals, the strong form and the section 16 readings
sound; its own reimplementations matched every figure of 6.1.

| finding | what draft 4 changed | where |
|---|---|---|
| V1: `before-first-shot` as defined was not what v0's links are; 8 kingston jobs fall in the history's lag | the links are `history-at-first-shot` and `history-at-running`, what the read computed. `history-in-gap` names the 8 jobs whose first shot followed a newer snapshot's stamp and measurements. Control `calibration-gap`. The lag is measured: 9.0 to 9.4 minutes | 4.5, 6, 6.1, 11, 12 |
| V2: "the morning law jobs ran … interleaved" was false | no job of the day was interleaved: each device's jobs form one block, morning and sheets (MEASURED) | 0, 4.4, 6, 6.1, 9, 12 |
| V3: "one status per cause" did not hold in 6.1 | one status per cause per measure, from four statuses, UNMEASURED with its absence word. What both runs share is listed as unseen, not as a status | 6, 6.1, 8, 14 |
| V4: "IBM's 0.50.0 interface does not" name a job's calibration was broader than what was read | `properties()` is a client-side match. The runtime can carry and send an optional `calibration_id`; none of v0's metrics has one. Requesting one is in question 9 | 3, 6, 14 |
| V5: "moved" had an unstated baseline, and the instrument said "frozen against" for 56 jobs frozen against later snapshots | every comparison names the morning freeze. The sheet freezes are listed and compared where carried; kingston's, 11:05:15Z, is in no record | 4.5, 6.1, the calibration instrument |
| V6: four inverted shot counts were one shot short of their rule | each count is the least whole count that meets its rule, checked both ways | 16.5, the sufficiency instrument |
| V7: "only the stamps had moved" was false in letter | the 2 marrakesh values are named, and the moved per-value dates stated. The records README is corrected by a dated entry | 0, 4.5, records/2026-10-14/README.md |
| V8: a READ citation no longer supported its bullet | draft 2's wording restored | 12 |

**The re-check's notes, taken:**
- **section 0:**
  - item 6 is labelled exploratory, at ε = 0 (N2);
  - its shot counts are tied to the Hellinger {device} test (N5);
  - "attributed only to", with `unknown` factors named (N10);
  - the dephased values are BELIEVED (N14);
  - "afternoon" is replaced by the sheets' times (N13);
- **drift and statuses:**
  - "the two runs' bounds together exceed the difference" (N3);
  - CONTROLLED is read as "a certified bound exists", with tightness
    the strong form's question (N3);
  - Atlas's sampling is CONTROLLED under the same model, its sampler
    `unexposed` (N11);
  - absence words are given (N17);
  - the time-block qualifier is moved out of the conditions (N18);
- **planning:**
  - the proposed nine-job campaign, M = 9 (N4);
  - R stated as v0's maximum taken as the true risk (N4);
  - only law jobs are costed (N4);
  - 247 s were left after v0 (N4, N15);
- **the reads:**
  - their limits, results not digests, and files not the commit, are
    stated in 12, and question 9 asks for digests (N6);
  - storage time is marked as an inference (N7);
  - the `properties()` bullet is reworded (N7);
  - kingston's sheet freeze is not carried (N16);
- **the comparison:**
  - the pooled target's weights;
  - `selector-late` covers tolerances;
  - at ε = 0 the verdicts are differ or unresolved;
- **the rest:**
  - the confirmation list gains draft 3's own decisions (N9);
  - the "where" column for R7 and R10 is corrected (N12);
  - question 14 says kingston did recalibrate later.

**Not changed:**
- the `len(W) == 4368` conjunct is kept as a sanity check, and not
  claimed as a control;
- the cost model through the origin keeps `max` over the law jobs'
  charges, all 9 s on v0. It is the highest of the three at ε = 0.05;
  at ε = 0.10, model (c) is higher (draft 4's re-check, W3).

**New in draft 4, beyond the findings:**
- three cost models, over all 65 jobs;
- planning for a nine-job campaign;
- the history's lag and the gap jobs, measured;
- every job's created order, by device, measured;
- a dated correction appended to records/2026-10-14/README.md.

**The instruments, in draft 4:**
- **`sufficiency_v0.py`:**
  - least whole counts, checked both ways;
  - the M = 9 campaign;
  - three cost models;
  - each charge tied to its job by id, replacing a count that compared
    itself.
- **`calibration_at_execution_v0.py`:**
  - it refuses unless the read's MANIFEST, and every file it lists, hash
    as recorded. Two planted edits were refused;
  - the morning- and sheet-freeze baselines;
  - the predictions against their freezes;
  - the history's lag, and the gap jobs;
  - the coherence values held to the records;
  - dates compared as times;
  - a coupler lookup that keeps a 0.0.
- **`v0_timing_and_drift.py`:** the coherence values held to the
  records, and every job's created order.
- **`isolation_v0.py`:** unchanged.

**Draft 4's re-check** (W1 to W5, answered in draft 5). It confirmed V1 to
V8 answered and applied everywhere, and reproduced every new figure.

| finding | what draft 5 changed | where |
|---|---|---|
| W1: "by at least 0.044" rounded a certified lower bound up | 0.0438, and 0.0040 beside it | 0 |
| W2: docs/VALIDATION.md:1700 should be :1701 | :1701 | 14, the free-tier instrument |
| W3: "the most conservative of the three" is false at ε = 0.10 | the highest at ε = 0.05; model (c) is higher at ε = 0.10 | 17 |
| W4: "draft 3 goes next" was stale | drafts 1 to 4 went past verifiers, and draft 5 goes next | 13 |
| W5: the README correction credited the instrument with details it did not print | the calibration instrument now prints each changed value when there are ten or fewer: the coupler, its rise, and whether it is on the chain | the calibration instrument |

**The re-check's notes, taken:**
- **the history's lag:** "can return", bounded from below for one
  snapshot of seven; storage time marked BELIEVED (a);
- **citations:** `calibration_id` cited through the job-mode path,
  base_primitive.py:155-208, and :316 named a configuration request (b);
- **absence words** on every UNMEASURED (c);
- **marrakesh's 2 values** named beside "the morning freezes' values"
  (d);
- **the link:** chosen in a stated order, with `history-at-running`
  beside it (e);
- **the MANIFESTs:** only the first names moth-quantum's files (f);
- **the counts** cover the qubit and gate values; the `general` entries
  also show no difference (g);
- **the MANIFEST gate** also refuses a file it does not list. An extra
  snapshot was refused (h);
- **the output hashes** are of CRLF bytes (i);
- **the docstrings** are updated (j);
- **"Marrakesh's circuits"** do not use the coupler, not "v0's" (k);
- **"for the next verifier"** is now historical (l).

**New in draft 5, beyond the findings:**
- **section 9.1, the free-tier unit,** sized by `free_tier_unit_v0.py`.
  It covers:
  - the unit's recipe, cost and size;
  - what one unit and pooled units can certify, projected from v0's
    data;
  - pooling across crates, with looks spending α/(k(k+1));
  - the strong form at unit granularity;
  - readout for a difference, taking only the lower-reading device's
    shrinkage;
  - the standing pre-registration;
  - contributions from anyone;
- **the quantum-comparable level:** readout controls may sit in the job
  just before, under the same calibration values-digest;
- **question 9,** rewritten around the unit;
- **questions 15 and 16;**
- **parcel P5,** the contributor kit;
- **Logan's aim,** recorded verbatim.
- An appended line in records/2026-10-14/README.md notes when the
  instrument began printing the changed values.

**The instruments, in draft 5:**
- **`free_tier_unit_v0.py`,** new: it costs fifteen designs, then
  projects one unit's verdicts and the units pooled verdicts need;
- **`calibration_at_execution_v0.py`:** the MANIFEST gate also checks the
  directory's file set, and the changed values are printed;
- **`sufficiency_v0.py`** and **`v0_timing_and_drift.py`:** docstrings
  only;
- **`isolation_v0.py`:** unchanged.

**Draft 5's re-check** (X1 to X8, answered in draft 6). It confirmed W1 to
W5 and notes a to l answered, except note b in section 15. It
reproduced every figure of section 9.1 it recomputed, and derived the
signed readout bound independently.

| finding | what draft 6 changed | where |
|---|---|---|
| X1: "pooled units resolve the rest" was false, and unlabelled | a projection, with the cells that stay unresolved at 100 units named | 0 |
| X2: the anytime-validity claim was unscoped | a look's family is everything it computes, leaving each contributor out and the unit means included. Its scope is stated: what the standing pre-registration names, on a pool that only grows, with arrival independent of results | 9.1 |
| X3: "three devices" was labelled READ for every free account | READ for Logan's instance on 2026-10-05, BELIEVED for others. The standing pre-registration names the devices, and `unit-incomplete` covers a unit on fewer | 0, 9.1, 14 |
| X4: "in-job" readout wording contradicted the new level | "in the job or the job just before it", in section 6 and 6.1; 16.2 states the difference from the paper | 6, 6.1, 16.2 |
| X5: question 9 and 16.5 pointed at each other for costs | 16.5 carries the four nine-job costs | 16.5 |
| X6: section 15's runtime lines and report list were stale | base_primitive.py:127-208, sampler.py:125-140, and the re-checks of drafts 2 to 5 | 15 |
| X7: "the unit is a campaign" contradicted the standing pre-registration | crate, campaign and comparison defined separately | 9, 14 |
| X8: "the largest design costed" was false | "of the film designs", with the split design's trade and the 4,096-shot controls stated | 9.1 |

**The re-check's notes, taken:**
- **N1:** the unit's order shown afterwards from created and running
  times; `unit-incomplete` and `not-interleaved`, with controls in
  section 11;
- **N2:** the readout model's cross terms restored in the certified
  bound. The formula is stated in 9.1, with why section 6.1's +0.0034
  has none. One unit's margin fell from +0.0099 to +0.0040;
- **N3:** the labels name R, and the single-job plug-ins and their noise.
  They say the coherence projections are rough;
- **N4:** the strong form's shot needs measured (77,824, 153,600, and
  more than a million). For coherence it is not projected;
- **N5:** the standing pre-registration names its Hellinger object and
  its coverage, and how its date is shown;
- **N6:** `withheld` units are their own contributors. Flips at small k
  are labelled. The handle is added to rule 3's Carried list. An anchor
  records who made it, and a comparison counts others' anchors as
  REPORTED;
- **N7:** a pair's pool takes only units complete on both devices;
- **N8:** P5's control is in section 11. P5 runs in job mode and extends
  Quantum-Film's bundle format. sampler.py is a source;
- **N9:**
  - "share a calibration" is BELIEVED;
  - "no value difference";
  - section 15 names the file-set test;
  - the unit's iterations are "passes", not "rounds".
- **Section 8's ρ:** both offsets are named, and "beyond readout" is
  distinguished from "isolated as quantum".

**Not changed:** the checks the re-check found cannot fail on v0's data
stay, as guards for other data. None is claimed as a control:
- `beyond_readout`'s positivity guard and its B-above-A branch;
- the "on the chain" branch;
- the byte-count test beside the hash.

**New in draft 6, beyond the findings:**
- **Logan's hold,** verbatim: no real run until a functional prototype
  crate exists, and Logan's units through the same kit as a stranger's;
- **section 13's milestone M1,** in five stages:
  - the format;
  - v0 as crates;
  - a unit on runtime 0.50.0's local fake backends;
  - the comparison;
  - IBM's server-side `dry_run`, on Logan's word.

  M2 is the first real unit;
- **P5's three routes:** local, dry run and real, with one crate format.

**The instruments, in draft 6:**
- **`free_tier_unit_v0.py`:**
  - the readout bound's cross terms, from certified single-site means;
  - each look's family is everything it computes;
  - the 247 s and R are computed, not typed;
  - the strong form's shot needs;
  - 4,096-shot controls pooled;
  - "passes".
- The other six are unchanged since draft 5.

**Draft 6's re-check** (Y1 to Y4, answered in draft 7). It confirmed X1 to
X8, N1 to N9 and the ρ note answered. It derived the readout model and
property-tested the bound, and reproduced every figure of 9.1.

| finding | what draft 7 changed | where |
|---|---|---|
| Y1: "about half the sum of both devices' shrinkage" was left stale by N2 | the bound's parts, now printed by the instrument: 0.0238 is fez's shrinkage, 0.0181, plus both offsets, 0.0058. The shrinkage alone is about half of 0.0355 | 9.1 |
| Y2: "the checker refuses every planted control" could not be met | stage 2 meets each crate-level control as section 11 states it. P2's measures and exact hold join stage 2, and the unit's and comparison's controls wait for stages 3 and 4 | 13 |
| Y3: X7 was not applied everywhere | the Atlas runs are not a campaign; a crate's devices interleave; a run may be a set of crates | 8, 9 |
| Y4: HARDWARE.md:16-17 was dated 2026-10-05 | read 2026-10-01; v0 ran on all three on 2026-10-05; the probe lists them on 2026-10-14 | 0, 9.1 |

**The re-check's notes, taken:**
- **a:** stage 5 is now a read-only pre-flight, since this account lists
  no mock backend. The dry run stays a route for accounts that do;
- **b:**
  - the family count names the case of incomplete units;
  - the projection's constant readout across units is stated, with the
    two sound ways to pool readout without it;
- **c:**
  - the kit's routes name Quantum-Film's `kind`, and a local unit is
    its own `simulator` bundle;
  - a dry-run crate fails its known answer by design and is never
    pooled;
  - pooled comparisons admit only `qpu` units (control
    `dry-run-pooled`);
- **d:**
  - the kit's commit is in the body;
  - control `kit-dirty`;
  - the Atlas runner is cited for the dirty-tree refusal;
  - "same kit as a stranger's" is labelled this study's reading of
    Logan's reason;
  - M1's stages are on the confirmation list;
- **e:** the 247 s holds until 2026-11-02;
- **f:**
  - a coherence plug-in is a PUB;
  - the pair's qubits are numbered 1 and 2, apart from devices A and B;
  - the strong form's shot needs are exact: 77,380 and 153,166;
  - the fake backends' dates are cited to their property files;
  - `qro:role` is per PUB. P5's repeated negative control was already
    removed.

**New in draft 7, beyond the findings:**
- **Logan's word on dry runs,** verbatim.
- **The read-only probe** of 2026-10-14 (`ibm_dryrun_v0.py --probe`). It
  found:
  - plan `open`, with three backends and no mock backend;
  - 353 of 600 seconds and 5.448 of 10 resource units used;
  - a rolling window.
- **Stage 5 rewritten** around the probe's findings.
- **Section 9.2, federated custody,** with Logan's aim verbatim:
  - three roles: producer, custodian and auditor;
  - audit records and custody logs;
  - disagreement is a finding;
  - degrees of independence;
  - provider custodians;
  - the Moth-then-ASU pilot;
  - the coin toss engine as a QRO question.
- **The pilot in the rest of the study:**
  - section 0 item 9, and a limit in section 12;
  - M1 stage 6, a second custodian;
  - the formats in P0;
  - questions 17 to 19.

**The instruments, in draft 7:**
- **`free_tier_unit_v0.py`:** prints the readout bound's parts, and
  finds the strong form's least shots by bisection.
- **`ibm_dryrun_v0.py`,** new: its `--probe` is read-only, and its
  `--submit` refuses without a mock backend. Only the probe ran.
- The other six are unchanged since draft 6.

**After draft 7's freeze:**
- Logan decided question 18 on 2026-10-14: "CC BY 4.0 for the data
  licence works".
- That is recorded in the header, in the decided questions, and in
  section 9.2.
- Logan then settled the code's licence, the licence part of question
  10: "MIT for the code license works too, unless it would be simpler to
  keep both CC BY 4.0".
  - The lead advised against CC BY 4.0 for code, so the code is MIT and
    the crates' data CC BY 4.0.
  - `git init` and the public repository stay open.

**Draft 7's re-check** (Z1 to Z12, answered in draft 8). It confirmed Y1 to
Y4 answered, and reproduced every output byte for byte.

| finding | what draft 8 changed | where |
|---|---|---|
| Z1: stage 4 pooled `simulator` units that "pooled comparisons" refused | a comparison is declared real or a rehearsal. A real one admits only `qpu` units, refusing others as `kind-not-qpu`; a rehearsal says so in its body and is never cited. Control `simulator-in-real` replaces `dry-run-pooled` | 11, 13 |
| Z2: "dry run unavailable" rested on the listing alone | a second read-only probe looked each mock backend up by name: IBM answered 404 for all three. The inference left the Decided list | header, 13, 14 |
| Z3: an independent checker called "an external authority" | none of the three degrees is one; HonestFramework's own words quoted | 9.2 |
| Z4: a provider's own records called ANCHORED | they anchor other producers' runs, for an auditor who fetches them; its own runs stay REPORTED until signed | 0, 9.2, question 17 |
| Z5: "each step is linear, so averaging is sound" | the shrinkage and a·m' terms are linear, and the sum is over both qubits. The a_1·a_2 term takes the largest unit's other absolute a | 9.1 |
| Z6: "two IBM tools" | three | header, 15 |
| Z7: stale draft numbers | drafts 1 to 7, and draft 8 next; re-checks of drafts 2 to 7 | 13, 15 |
| Z8: the Atlas runner cited at 149-153 | 150-155 | 13 |
| Z9: "IBM reported the same 247" | IBM reported 600 and 353; the client computes 247. The records README is corrected by a dated entry | 9.1 |
| Z10: Moth's records could lift v0's Atlas crate | v0's Atlas crate stays "recorded"; future runs could carry the compile and a held commitment | 9.2, question 19 |
| Z11: no trusted-time slot was named | both slots are named, on every crate's root and in every audit record | 9, 9.2 |
| Z12: the coin toss called unread, against Moth's description in v0's records | Moth's description cited. One qubit, so correlations between qubits drop; counts only, so correlations between shots cannot be audited | 0, 9.2 |

**The re-check's notes, taken:**
- **checker steps and controls:** each has a parcel (section 13);
- **stage 5:** "the last check against IBM";
- **stage 2:** writes the Atlas crate too;
- **audit records:** the degree of independence is REPORTED. Rule 3 now
  covers auditors' and custodians' handles;
- **custody logs:**
  - each line hashes the one before (control `custody-chain`);
  - withdrawal is the one exception to keeping both;
- **labels:**
  - "IBM attests to no one's records but their owner's" is BELIEVED;
  - Moth's `qpu` mode makes Moth the IBM job's owner;
  - the pilot's order is Logan's, and what each group might do is the
    study's;
- **readout and drift:**
  - the across-units routes add intervals beyond the 579;
  - the parts of the bound are rounded separately, and are for ⟨X0X1⟩;
  - marrakesh against fez never clears the strong form under v0's
    drift. The instrument prints the limit, −0.0227;
- **the instrument:**
  - the bisection asserts its low end fails;
  - its docstring numbers the qubits 1 and 2;
- **the kit:**
  - `kit-dirty`'s untagged-commit rule is this design's own;
  - the kit's commit joins cause 3's definition;
  - M2 is labelled this study's reading of Logan's reason;
- **wording:**
  - "(section 9 and rule 4)", and "this study's section 10";
  - the coin's twin is the fair coin.

**Not taken:** "ASU" stays as Logan wrote it.

**The instruments, in draft 8:**
- **`free_tier_unit_v0.py`:**
  - the strong form's limit as shots grow;
  - the bracket assertion;
  - the docstring.
- **`ibm_dryrun_v0.py`:**
  - the by-name lookup;
  - the URL-quoted CRN refusal;
  - `--submit` gated on the lookup.

  Only `--probe` has run.

**Draft 8's re-check** (AA1 to AA3, answered in draft 9). It confirmed Z1 to
Z12 answered and applied everywhere. The second probe, the licences, the
instruments, the sweep and the privacy scans were clean.

| finding | what draft 9 changed | where |
|---|---|---|
| AA1: a withdrawal "marked" a line of an append-only, hash-chained log | the line stays unaltered, and a later line records the withdrawal. Controls `withdrawal-in-place` and `withdrawal-appended` | 9.2, 11 |
| AA2: "an edited or dropped line shows" is false for the last line | stated as a limit; an audit record carries the log's head hash. Control `audit-head-mismatch` | 9.2, 11 |
| AA3: "the other five are unchanged since draft 6" | six | 17 |

**The re-check's notes, taken:**
- **section 8:**
  - `kind-not-qpu` is among the refusals, with the real-or-rehearsal
    declaration;
  - v0's Atlas crate is kind `simulator`;
- **wording:** "resolve", not "lists", in 9.1, P5 and the tool's
  docstring;
- **ownership:**
  - P0 owns the custody-log check;
  - P5's controls name `kit-dirty`;
- **cause 3:** the producing commit is `partial` for v0, in section 6's
  table and in 6.1;
- **the root's two slots** are in the header, and `none` in v0;
- **"dry run unavailable":** what was MEASURED, two lookups, is kept
  apart from what was READ, the refusal path. The docstring's "may be
  restricted" is cited;
- **the tools:**
  - the dry-run tool no longer rebinds `by_name`;
  - the sizing instrument's bracket check is a refusal that `-O` cannot
    strip;
  - its stale comment is fixed;
- **the records README** notes the log's line ends, the settled "would
  refuse", the scratch trial, and the tool versions;
- **licences:**
  - CC's advice is quoted, attributed to draft 8's re-check;
  - Logan's condition goes to the confirmation list;
  - the providers' terms are BELIEVED and Logan's to check;
  - the documents' licence joins question 10;
- **small points:**
  - Moth's qpu-mode ownership is BELIEVED;
  - "question 17" and "question 19" in the "where" column;
  - question 17 names the hash chain and withdrawal;
  - an audit record is not a comparison;
  - the coin toss returns its counts, its shots and its majority side;
  - a Bell test needs two or more qubits.

**Not changed:** the pooled analysis of v0's IBM crate against Atlas
stays a rehearsal, and `question-differs`, as section 8 says.

**The instruments, in draft 9:**
- **`free_tier_unit_v0.py`:** the bracket refusal and a comment. Its
  output is unchanged.
- **`ibm_dryrun_v0.py`:** a renamed variable and the docstring. No
  probe ran with this version.
- The others are unchanged since draft 8.

**Draft 9's re-check** (AB1, answered in draft 10). It confirmed AA1 to AA3
answered and applied everywhere. It modelled the custody log as specified
and found it behaves as the text says.

| finding | what draft 10 changed | where |
|---|---|---|
| AB1: two stale draft numbers, the fourth recurrence of W4, X6 and Z7's slip | corrected. The new gate `check_study.py` read two sentences, section 13's and section 15's, against the header's draft number, wherever they stood, and refused draft 9 for exactly AB1. From draft 11 the gate reads six, each in its own place (section 15) | 13, 15 |

**The re-check's notes, taken:**
- **N1:** `withdrawal-in-place` needs a line after it;
- **N2:** the producing commit counts as EQUAL only where it is recorded;
- **N3:**
  - a comparison declares real or rehearsal;
  - 6.1 is declared real;
  - Atlas's `simulator` kind rests on its 20 of 20 `emu` records;
- **N4:** the head hash's four conditions are stated:
  - the first line's predecessor is fixed;
  - an auditor with no log gives `none`;
- **N5:**
  - the log-tail limit is in section 12;
  - stage 6 holds the custody controls;
- **N6:** `partial` is replaced by `unknown` per job, and the Atlas cell
  names `code_commit`;
- **N7:** `none` replaces "empty", and rule 4's header names the slots;
- **N8:** Moth's description "claims no more";
- **N9:** the dry-run conclusion is labelled an inference from MEASURED
  and READ parts;
- **N10:** Logan confirms the code licence at approval, and the documents'
  licence is "proposed";
- **N11:** the redundant clause is dropped;
- **N12:** the instruments run without `-O`, as section 15 says. The
  records README's later notes say which tool version gated what.

**Not taken:**
- **N9's note on the instance.** The probe passed the instance, and the
  runtime's dry-run lookup does not. For a service bound to one instance,
  as account.connect builds it, they agree. That is BELIEVED, not
  re-tested.
- **N12's suggestion of a control** for the bracket refusal. Section 11's
  controls are crates', not instruments'. The verifiers plant the
  instruments' faults.

**The instruments, in draft 10:** `check_study.py`, new. The rest are
unchanged since draft 9.

**After draft 10's freeze:**
- Logan, 2026-10-14: "MIT confirmed, docs CC BY 4.0, go ahead with git
  init".
- So the licences are decided, and recorded in the header, the decided
  questions and question 10.
- The repository is initialized on `main`, with `LICENSE`,
  `LICENSE-docs.md` and `.gitattributes` (`* -text`). Nothing is
  committed.

**Draft 10's re-check** (AC1 to AC3, answered in draft 11). It confirmed AB1
fixed, and that the gate refused all five fault classes it planted. It
modelled the custody log, as draft 10 specified it, with 6,000 random
tampers and no mismatch.

| finding | what draft 11 changed | where |
|---|---|---|
| AC1: rule 4's "That last" pointed at the new slots, not `datePublished` | the quotation names `datePublished` | 5 |
| AC2: the study claimed more for the gate than it checks | the gate now checks: the header's and section 17's draft labels; the sentences of sections 13 and 15 within their own sections; a stale copy of a header, section 13 or section 15 sentence beside a right one; indented tables and delimiter rows; capitalised, listed and wrapped references, and both ends of a range; one parsable row for every instrument. Section 15 and its docstring state its limits | header, 15, the gate |
| AC3: "each refuses unless moth-quantum is a clean 3a73823" was false for the gate | the gate is excepted, and the header names it | header, 15 |

**The re-check's notes, taken:**
- **1:** 6.1's five cells name the producing commit's `unknown` as a
  stopper, and short answer 2 names the producing commit;
- **2:** Atlas's `simulator` kind:
  - section 8 sets out READ facts and an inference: the account
    had no hardware feature, the six law jobs were its, and their request
    left the engine's provider at its default, `aer`;
  - the two `emu` lines the re-check named are in VALIDATION.md's
    entries of 2026-09-25, about those entries' own jobs. Section 8 cites
    them as such, not as the law jobs';
- **3:** the head hash has two conditions, an effect and a limit. An empty
  or absent log gives `none`, and an honest `none` cannot be told from a
  withheld one;
- **4:**
  - section 10 names the custody-log check;
  - the Bell test's two systems are BELIEVED;
  - question 15 matches section 9.1: a contributor's anchors are
    REPORTED except in a comparison the contributor wrote;
- **6:** 4.3's state words are said to describe the records, not a
  crate's fields;
- **7:** section 15 says who runs the gate, and when;
- **N9 at question 9:** MEASURED, READ and the inference are separate
  lines.

**Not changed:**
- **Note 5**, draft 10's line 2105, whose "decided" disagreed with the
  header. The live file had resolved it after the freeze.

**The lead's checks before the freeze** (MEASURED, 2026-10-14, with the
five instruments and `plants.py`, a scratch script given to draft 11's
verifier):
- the five analysis instruments, re-run on a clean 3a73823, each wrote
  its kept output byte for byte;
- 26 faults planted in copies were each refused by name:
  - stale draft numbers, a stale copy beside a right one included;
  - short body and delimiter rows, in indented and spaced tables too;
  - references to sections that do not exist: capitalised, wrapped,
    listed and at a range's end;
  - in section 15's table, rows that do not parse, a missing row, an
    extra tool, and a changed byte in a tool, an output or the gate;
- 4 right variants were accepted: the draft itself, a wrapped
  sentence, older drafts' labels in section 17, and a reference just
  after a ".md" name, skipped as stated.

**The instruments, in draft 11:** `check_study.py`, strengthened. The rest
are unchanged since draft 10.

**Draft 11's re-check** (AD1 and AD2, answered in draft 12). It
confirmed AC1 and AC3 fixed, notes 1 to 7 and N9 right, and each of
note 2's facts at its cited place. It re-ran `plants.py`, with the same
log, and the five instruments, each byte for byte. It repeated the
clone trial, with the same counts.

| finding | what draft 12 changed | where |
|---|---|---|
| AD1: draft 10's AB1 row still said the gate "refuses any draft whose numbers disagree with its header" | the row says what draft 10's gate read: two sentences, wherever they stood. Draft 11's AC2 row names the header too | 17 |
| AD2: the gate skipped an output-hash cell it could not parse, so a wrong hash in another form passed | a row that names an output must parse, or the gate refuses | 15, the gate |

**The re-check's notes, taken:**
- **1 to 3, the gate's unstated limits.** The gate now checks most of
  them:
  - every pipe-led line must belong to a table, and every row must end
    with a pipe. So blank and prose lines inside a table, a header below
    a pipe-led line, a two-hyphen delimiter, and a row with a cell more
    but no trailing pipe are refused;
  - every delimiter cell is read;
  - "section" in any case, and lists joined by "or", a slash, a hyphen
    or an en dash, are read, and so are section 17's "where" cells;
  - a duplicate row, an unlisted file and a subdirectory in qro0/ are
    refused.

  Section 15 and the docstring say it checks nothing else, and list
  what that leaves.
- **4:** the clone trial and draft 11's checks name what measured them.
  The plants are kept as an instrument, `check_study_plants.py`;
- **5:** the producing commit is named in sections 0, 6.1 and 12, and
  6.1's "isolated as quantum?" cells name every cause that stopped them;
- **6:** sections 4.1 and 4.3 no longer state Atlas's emulator as READ;
- **7:** 4.3's legend says which of its states are rule 2 words;
- **8:** draft 11's "line 2105" names draft 10's numbering;
- **9:** `.gitattributes`'s comment counts the three CRLF records logs,
  and says Quantum-Film's vector "would have" failed.

**Not changed:**
- **Note 10,** `LICENSE-docs.md` names CC BY 4.0 by its URL and carries
  no legal code. That is Logan's to decide.

**The lead's checks before the freeze** (MEASURED, 2026-10-14):
- the five analysis instruments, re-run on a clean 3a73823, each wrote
  its kept output byte for byte;
- `check_study_plants.py`: 51 faults refused by name, 4 right
  variants accepted, none unplaced.

**The instruments, in draft 12:** `check_study.py`, strengthened, and
`check_study_plants.py`, new. The rest are unchanged since draft 11.

**Draft 12's re-check:** READY, with no defect, and notes N1 to N9. It
re-ran the plants, with the same log, and repeated the clone trial on
draft 12's tree. It also showed that a plant then passed on any named
failure, not only the one it targeted: of 55 copies of the gate, each
broken at one point, the plants caught 38.

**The approval,** 2026-10-14. Logan approved draft 12 (`f8a983e9…`) as
the plan of record, with every recommendation as written (section 14).

**The amendment,** the same day. It takes the notes, and Logan decided
note 10. The gate and the plants checked it; no verifier did.

| note | what the amendment changed | where |
|---|---|---|
| N1: a "where" cell's number after ", and" was not read | the gate reads it | 15, the gate |
| N2: "every copy" read wider than the gate's own places | the gate refuses a stale copy of the four sentences anywhere in the header and sections 13 and 15 | 15, the gate |
| N3: unchecked cases that no claim named | the header's date, swapped outputs, stale copies elsewhere, and the Contents list are named as unchecked | 15, the gate |
| N4: forms that refuse wrongly | the gate is said to fail closed, naming what it read | 15, the gate |
| N5: a plant passed on any refusal | each fault names the failure it expects. New plants cover the gaps the re-check listed, the unprintable character among them | 15, the plants |
| N6: the plants' robustness | a time limit for each run, LF copies, a plant with nothing to plant in counted as unplaced, and Python 3.11 or later stated | 15, the plants |
| N7: 4.1's "on its emulator" stood as READ | it says which jobs are READ and which inferred | 4.1 |
| N8: question 10's counts were draft 11's tree | dated, with draft 12's re-check's counts beside them | 14 |
| N9: two words | draft 12's note 9 says "counts"; the header says note 10 was Logan's | header, 17 |
| note 10: `LICENSE-docs.md` names CC BY 4.0 by link only | nothing: Logan, 2026-10-14, "A link is fine rather than full legal text as well" | header, 14 |

**The lead's checks after the amendment** (MEASURED, 2026-10-14):
- `check_study.py`: ACCEPTED;
- `check_study_plants.py`: 68 faults refused with the failure each
  targets, 6 right variants accepted, none unplaced.

**The instruments, after the amendment:** `check_study.py` and
`check_study_plants.py` changed. The rest are unchanged since draft 11.

**Later the same day,** before the first commit: the verifiers' twelve
reports, until then only in the session's scratch space, were placed in
docs/reviews/QRO-0/, home paths redacted. Section 15 now says where they are.

**And a correction, the same day.** The amendment's script wrote the
plants' two figures, in the lead's checks above, as unfilled placeholders.
They are filled from `check_study_plants.py`, run on the amended study
before the first commit: 68 faults refused, 6 right variants accepted,
none unplaced, none wrong. The plants and the gate are unchanged since the
amendment.

**The providers' terms, read the same day,** for question 10. A research
agent read IBM's and Moth's published terms.
- It found no clause of IBM's that limits publishing what the records
  hold, and no published terms of Moth's.
- It recommended a public repository, after named changes. They were made
  before the first commit:
  - LICENSE-docs.md scopes CC BY 4.0 to what Logan made;
  - NOTICE.md lists the providers' content, the terms read and the date;
  - the README carries IBM's suggested acknowledgement.
- The public repository waits on Logan's word.

**A correction, after P0's second verifier.** "Later the same day", above,
and section 15 said only that the reports' home paths were redacted. Seven
of the twelve had also lost a task notification's wrapper, and their CRLF
line ends (P0's second verifier, R2-8). docs/reviews/QRO-0/README.md now
states every change, per file. Section 15 points to it.

**Question 10, decided, 2026-10-15.** Logan: "When we push, go ahead with
a public repo, I will ask Moth directly about the data licensing situation
when available." So the repository is made public at its first push, once
P0's verifier finds P0 ready. That day IBM's two service descriptions were
read again, both unchanged (NOTICE.md).

**A correction to control `qpy-only`, 2026-10-15, from P1's design.**
Section 11's row said the plant recomputes the digests and the
commitment and leaves the gate list. In moth-quantum, the commitment
binds the QPY file's own digest (quantum_film/ibm/bundle.py:7), and
IBM's echo of the commitment sits inside the raw result. P1's design
found, on kingston's morning known-answer job, that a step 4 held to the
echo refuses the plant as the row worded it, `commitment`, and accepts
it only when the echo inside the raw result is rewritten and its digest
recomputed too. The row now says so. The control's verdict, accepted by
the crate-only checker as a stated limit, is unchanged. The round's
ledger holds the design; docs/VALIDATION.md records it (P0.3).

**Four amendments, 2026-10-15, from P2's and P4's designs.** Both designs
are in the round's ledger; docs/VALIDATION.md records them (P0.3).
- **The exact hold is step 7, on the crate alone.** Section 9's compile
  row said CHECKED where the stage runs, and section 10 listed the exact
  hold among four checks that need more than the crate. P2's design held
  v0's 124 gate lists, 12 of them distinct, to their logical circuits on
  the standard library alone, the worst at 5.4e-17 against 1e-10, in
  33 s on a loaded machine. So the row now says CHECKED
  (step 7), section 10 lists three checks, and the audit stage
  `exact-hold` is retired. Quantum-Film measured its rounding at 6.3e-17
  (isa.py:31-49, READ).
- **Step 6 holds the law table to the question's own law circuit,** by
  simulating it, besides its sum, digest and support. Without that, a law
  table edited with every digest recomputed would pass a crate with no
  compile. Nothing is derived from a kernel, so section 10's rule stands.
- **Section 6.1's intervals are narrower than the sets they claim,** by at
  most 1.9e-15. `isolation_v0.py`'s float bisection returns the last point
  it judged inside, and P2's design measured that 82 of its 140 endpoints
  lie inside the KL set. No figure moves at four places. QRO-Crate's
  certified intervals are P2's, rounded outward in integer arithmetic.
- **Each declared profile's contextual entity, as section 3 says.** P0
  wrote none, and its reader required none: P4's design found it. The
  reader now holds both, this profile's and Process Run Crate's, with
  their versions. The profile's IRI is now its description page, the
  README.md that P4 writes in profile/.
