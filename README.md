# QRO-Crate

An RO-Crate profile for quantum computing runs, built so that the difference
between two runs can be attributed: to the question, the compile, what was
submitted, the sampling, readout, the device's state and time, or drift
within a run. Its first data are Quantum-Film's runs, on IBM's processors and
on Moth's Atlas emulator.

**Status, 2026-10-15.**
- The design is study QRO-0, [docs/studies/QRO-0.md](docs/studies/QRO-0.md).
  Logan approved its draft 12 as the plan of record on 2026-10-14, and it was
  amended the same day for its last re-check's notes.
- P0 is built:
  - the vocabulary table, and the files generated from it;
  - the canonical writer and the strict reader;
  - the checker's steps 1, 2, 3 and 9;
  - the custody log and the audit record;
  - the controls' registry;
  - the runner.
- P0's verifier found it READY in its sixth and last round, on 2026-10-15,
  to the bar Logan set: no defect in what the code does.
- P0.1, the lead's, takes that round's notes and prepares the files that
  parcels building at once would share: each parcel's checker code, plants
  and tests go in files of its own, and P1's, P2's and P4's stages are
  already written. Each round of its verifier, what it found and what was
  fixed, is in docs/VALIDATION.md, and each report in docs/reviews/P0.1/.
  Its fourth verifier found it READY, and it was committed on 2026-10-15.
- P0.2, the lead's, takes that verifier's notes, past a verifier of its
  own, before the parcels build. P1's, P2's and P4's designs are
  approved; P0.3, the lead's, prepares the shared files their builds
  need.
- Nothing else is built: no adapter, no measures, no comparison, no profile
  crate, no contributor kit. A crate holding a field that steps 4 to 8 of
  the checker would check is refused `step-unbuilt`.

**Check it:** `bash verify/run.sh --budget quick`. CLAUDE.md says what will
bite you; [docs/README.md](docs/README.md) indexes the documents.

**Licences:**
- code is under MIT ([LICENSE](LICENSE));
- documents and data are under CC BY 4.0, over what Logan made
  ([LICENSE-docs.md](LICENSE-docs.md));
- provider content keeps its owners' terms, and [NOTICE.md](NOTICE.md)
  lists it.

**Acknowledgement.** We acknowledge the use of IBM Quantum services for
this work. The views here are Logan's own, not IBM's or the IBM Quantum
team's. IBM, IBM Quantum and Qiskit are trademarks of International
Business Machines Corporation, registered in many jurisdictions worldwide.
This repository is not affiliated with, or endorsed by, IBM or Moth
Quantum.
