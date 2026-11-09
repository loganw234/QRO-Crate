# Notices: what here is not Logan's

[LICENSE-docs.md](LICENSE-docs.md) grants CC BY 4.0 over what Logan W.
made. This file lists what came from others, which terms were read, and
when.
- The terms were read on 2026-10-14, for study QRO-0's question 10, by a
  research agent reading the providers' public documents. That is a
  reading, not legal advice.
- IBM's two service descriptions were read again on 2026-10-15, the day
  Logan decided the repository goes public. IBM's terms site lists each
  as its active version, unchanged:
  - i126-9425, v10, published 2026-08-06;
  - i126-6605, v29, published 2026-09-29.
- Moth Quantum's data and licensing are Logan's to settle with Moth
  directly. No file of Moth's is kept here (below).
- When a crate carries a provider's file, this file lists it.

## IBM

**What is IBM's.** Data IBM Quantum's service returned to Logan's account,
kept in records/2026-10-14/:
- **Seven calibration snapshots,**
  `ibm-refetch/<device>/properties-<stamp>.json`. They are IBM's
  backend-properties snapshots for ibm_fez, ibm_kingston and ibm_marrakesh,
  as IBM's history returned them, carried as provenance. **No licence is
  claimed over them,** and CC BY does not cover them.
- **Fields of each job's document and metrics,** in the 65 files
  `ibm-refetch/<device>/<job id>.json`:
  - the backend, times, job and program ids, status, usage figures and
    options, as IBM reported them;
  - the usage's metric id, a UUID, the same in all 65 records. IBM's API
    reference calls it the identifier of the metric definition the usage
    was calculated from. Whether that definition is IBM's for every
    account, or this account's own, is not established (P0's second
    verifier, READ).
  - the names, and only the names, of the parameters' keys. No circuit is
    kept.
- **The account's plan and usage, as IBM reported them,** in
  `ibm-dryrun-probe/` and `ibm-dryrun-probe-2/`: the plan, its pricing
  type, the backends listed, and the usage figures and their period.
- **The tools' logs** quote the IBM client's warnings.
  ibm-dryrun-probe-2.log also quotes IBM's three error responses, their
  request trace ids redacted.

**What is Logan's,** in the same files:
- the comparison flags (`holds`), the calibration pointers, the fetch
  times and the roles;
- every digest, size and manifest.

ibm-results-refetch/ holds no result content. It has only the SHA-256
digests and byte counts of the text IBM returned, compared with
Quantum-Film's committed copies.

**What was left out:**
- the job document's `user_id`, `cost` and
  `estimated_running_time_seconds`;
- the metrics' `circuits_execution_time_ns`;
- the usage's instance and plan ids.

The API key and the instance's CRN were never written in this repository.

**The terms read, 2026-10-14:**
- the IBM Cloud Services Agreement, Z126-6304 v13, published 2023-08-28,
  or its successor:
  - the Client Relationship Agreement, Z126-6548 v13;
  - with its Cloud Services attachment, Z126-6560 v09, effective
    2026-08-17.

  Which of the two governs Logan's account was not determined. They agree
  on every point below.
- the IBM Cloud Service Description, i126-6605 v29, effective 2026-09-30;
- the IBM Quantum Compute Service (Beta) Additional Service Description,
  i126-9425 v10, published 2026-08-06, which holds the Open Plan's terms.

**What they say, as read:**
- A client's inputs are its Content, and using the service does not
  change who owns them.
- No clause was found that limits publishing job metadata, results,
  calibration data or usage figures.
- No clause allocates outputs.
- None of them licenses IBM's own data.

**Limits on using the service, as read.** These bear on how the service
is used, not on what may be published:
- research and development use only, not part of a commercial offering
  (i126-9425 §5.4);
- the client's own use, and its contractors' (§5.6);
- a review of applications for responsible use (§5.3), restricted
  countries (§5.7), and one Open Plan account a user (§5.8);
- no reverse engineering and no resale (Z126-6304 §1.h);
- the service is a Beta (i126-9425 §5.1 and §5.2; Z126-6304 §1.i), and
  IBM gives 30 days' notice of changes to its service descriptions
  (i126-6605 §6.1.3).

**Acknowledgement.** IBM's FAQ suggests this form: "We acknowledge the use
of IBM Quantum services for this work." The views here are Logan's own,
not IBM's or the IBM Quantum team's.

IBM, IBM Quantum and Qiskit are trademarks of International Business
Machines Corporation, registered in many jurisdictions worldwide.

## Moth Quantum

- **What is Moth's.** No file of Moth's data or text is kept here. The
  study, docs/studies/QRO-0.md:
  - quotes short passages of Moth's published engine descriptions and
    documentation, attributed;
  - names Atlas engines by id.
- **Terms.** None were found, as of 2026-10-14. These places publish no
  terms of use, API terms or hackathon rules:
  - Moth's site;
  - Atlas's sign-in page, documentation and API specification;
  - the hackathon's site and repository.

  The terms Logan accepted at Atlas sign-up were not read.
- **Atlas's engine descriptions are not carried.** They are Moth's text,
  and they state no licence.

## Quantum-Film

- **What is kept, and where.** `tests/p1/data/moth/` holds 56 files of
  Quantum-Film's, copied byte for byte from the moth-quantum repository at
  3a73823 for P1's twin (docs/P1.md, "The twin and the controls"). They are
  test data: the twin is built from them at stage time, and the tree carries
  no other file of Quantum-Film's. By the path under `docs/records/`:
  - `2026-10-05/ibm/ibm_kingston/bundle/`: ibm_kingston's morning bundle,
    18 files (four circuits, each as `.qasm`, `.qpy`, `.isa.qasm3` and
    `.gates.json`, with `manifest.json` and `README.md`);
  - `2026-10-05/ibm/ibm_kingston/run/`: the runs of two jobs, the known
    answer and the coherence job, 12 files (job line, metrics, PUB records,
    raw result, submit record and verdict);
  - `2026-10-05/ibm/ibm_kingston/sheet-01/` and `sheet-02/`: the known
    answer's circuit files and run of two later sheets, 12 files each;
  - `2026-09-25/p3/circuit-ed767c01bd4b851d.qasm`: the source circuit.
- **The licence.** All 56 files are MIT-licensed, Copyright (c) 2026 Logan
  W.: the licence text is tests/p1/data/moth/LICENSE, one of the 56, and
  its notice is to stay with every copy. A crate P1's adapter builds from
  them carries it as `LICENSE-quantum-film`.
- **What is not Quantum-Film's in them.** The run files wrap IBM's job
  documents and raw result text, which are IBM's data (above): no licence is
  claimed over IBM's part, and the MIT licence is Quantum-Film's over its own
  records and code.
- **The vendored runner code.** The contributor kit (P5) carries 22 modules of
  Quantum-Film's runner, with its MIT notice; they are named in the next
  section.

## Quantum-Film's runner, vendored in the contributor kit

- **What is kept, and where.** `qro_kit/_vendor/` holds, byte for byte from the
  moth-quantum repository at 3a73823 (commit 3a738230286385664cd83c9c0a04fe33a5e2348a),
  the 22 modules of Quantum-Film's runner that the kit's driver needs, 194,424
  bytes, and two more files:
  - the modules, under `qro_kit/_vendor/quantum_film/`: `__init__.py`,
    `atlas/__init__.py`, `atlas/decode.py`, `atlas/pauli_tile.py`,
    `circuits/__init__.py`, `circuits/givens.py`, `circuits/givens_line.py`,
    `fixer.py`, `golden/__init__.py`, `golden/binomial.py`, `golden/fermi.py`,
    `golden/uniform.py`, `ibm/__init__.py`, `ibm/account.py`, `ibm/anchor.py`,
    `ibm/bundle.py`, `ibm/decode.py`, `ibm/isa.py`, `ibm/keyleak.py`,
    `ibm/raw.py`, `ibm/runner.py` and `stocks.py`;
  - `qro_kit/_vendor/LICENSE-quantum-film`, Quantum-Film's licence;
  - `qro_kit/_vendor/circuit-ed767c01bd4b851d.qasm`, the source circuit, a
    copy of the one in tests/p1/data/moth (above), which the kit ships so that
    a stranger needs no other file.

  `qro_kit/_vendor/VENDORED.sha256` lists each file's SHA-256 and size, and a
  changed byte fails tests/p5/test_p5_vendored.py.
- **The licence.** All 24 files are MIT-licensed, Copyright (c) 2026 Logan W.
  The notice is `qro_kit/_vendor/LICENSE-quantum-film` and is to stay with
  every copy. A crate the kit builds carries it as `LICENSE-quantum-film`.
- **What is not Quantum-Film's in them.** Nothing of IBM's or Moth's data is in
  these files: they are code, and the source circuit.

## Others

- **RO-Crate 1.3's JSON-LD context,**
  qro/data/ro-crate-1.3-context.jsonld, is CC0 1.0. qro/data/README.md gives
  its source and digest.

## No affiliation

This repository is not affiliated with, or endorsed by, IBM or Moth
Quantum.
