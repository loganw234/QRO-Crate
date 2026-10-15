# P0's format: where each rule is written, and what P0 chose

P0 is the lead's (study QRO-0, section 13). It makes exact what the study's
section 9 and rules 1 to 9 state, and chooses where the study left a choice.
Each rule is written once, in the code that enforces it or the table it
reads. This page points at it, and lists the choices, so that P0's verifier
can hold each one to the study.

## Where each rule is written

| rule | written in |
|---|---|
| terms, types, kinds, spellings, words, refusals, the custody and audit fields | qro/vocabulary.py, rendered as [VOCABULARY.md](VOCABULARY.md) and [REFUSALS.md](REFUSALS.md) |
| each spelling's one form | qro/spelling.py |
| the canonical bytes, the body and the crate's identity | qro/canonical.py, its docstring |
| the strict reader's order of decisions (step 1) | qro/reader.py, its docstring |
| the checker's steps 2, 3 and 9, the seam for steps 4 to 8, and its loading of each parcel's registrations (item 20) | qro/checker.py |
| the custody log, the audit record and the custody check | qro/custody.py |
| the controls of section 11 | controls/registry.py, rendered as [CONTROLS.md](CONTROLS.md); each parcel's plants in its own module beside it, merged by `plants()`; which are built, `python -m controls.run` says |

## The choices P0 made

1. **The context is inline:** RO-Crate 1.3's, then one object defining the
   prefix `qro`. A profile term is always written `qro:` and its name, so
   none can collide with, or silently redefine, an RO-Crate term.
2. **The namespace is provisional** (question 6): the generated vocabulary
   page, each term at its anchor. It resolves once the repository is public
   (question 10), and changing it is one row of qro/vocabulary.py.
3. **A term's kind is the table's, not written beside each value.** That is
   CERT-V2's field table, where a field's audit kind is the table's
   (cft-fp256's docs/studies/CERT-V2.md section 5, READ), and rule 9's "the
   vocabulary table gives each term its kind". Where the table says ANCHORED, a value is
   ANCHORED once the crate holds the provider's own record of it, and
   REPORTED until then; deciding which is the anchor stage's, not P0's.
4. **`term-unknown` and `field-kind` are told apart by RO-Crate 1.3's
   context,** pinned by digest in qro/data/ (CC0 1.0). A key RO-Crate defines
   but the table does not kind is `field-kind`, the study's "a field with no
   kind"; a key neither names is `term-unknown`.
5. **A rational is written in decimal,** `5/16`, where cft-fp256 writes hex.
   QRO-Crate's rationals are a law's probabilities, which a person reads.
   Every other rule of cft-fp256's rational is kept: lowest terms, the sign
   on the numerator, zero as `0/1`. Each term has at most 1,000 digits, so a
   reader never meets a number it cannot read. The same text `10/3` means
   different values in the two formats, so a reader names which it reads.
6. **No JSON `true`, `false` or `null`.** Absence has words (rule 2), and a
   yes-or-no is a word of a set.
7. **The header is a column of the table.** Its terms stand on the root, but
   `qro:implementation`, which stands on any entity whose definition's
   implementation it names (round 3, note 7).
   A crate's body is its arranged metadata with every header term removed;
   its identity is the SHA-256 of the body's canonical bytes.
8. **These refusal names are P0's own, where the study left a name open.**
   tests/docs/test_docs.py requires each of them here, every refusal name
   here to be the table's, and no count of them before this colon:
   - `file-missing`, `file-unlisted` and `file-digest` are step 2's
     "`raw-digest` and the like";
   - `file-link`, also step 2's, refuses a link in the crate;
   - `context` and `graph-form` are P0's additions to step 1's three
     names, `spelling`, `field-kind` and `term-unknown`: a wrong context and
     a misshapen graph are faults of another kind;
   - `metadata-generated` names step 9, which the study did not name;
   - `step-unbuilt` is the seam's own.
9. **A raw result is a `File` that is also a `qro:RawResult`,** naming its
   `qro:rawForm`. Its `qro:shots` are counted from its bytes by the form's
   reader. `qro:shots` stands only on a raw result, so a count on any other
   entity is refused at step 1 by its domain (item 13). A parcel whose
   entities carry a count of their own declares its rule in its module's
   `COUNTS`, which the checker loads (item 20).
10. **The root names its generator** (`qro:generator`). Step 9 runs it on the
    records and compares bodies byte for byte. The name carries no version,
    so changing a generator changes the bodies it makes: a crate written by
    another generator is another crate.
11. **A file's `@id` is its path in the crate, the same file on every host.**
    - Its segments use only RFC 3986's unreserved characters, its
      sub-delimiters but `*`, which Windows refuses in a name, and `@`,
      joined by `/`.
    - Refused: an empty segment, one longer than 255 characters, `.` or
      `..`, a segment ending in a dot, and a device's name, with or without
      an extension, in any case. Those are the names Windows reserves
      (`CON`, `PRN`, `AUX`, `NUL`, `COM1` to `COM9`, `LPT1` to `LPT9`),
      and four more it treats as devices in some places (`COM0`, `LPT0`,
      `CONIN$`, `CONOUT$`): a safe superset.
    - So no `:` (a drive, or an NTFS stream), no `%`, `#`, `?`, `\` or
      space. A crate holds no file whose name needs percent-encoding: a
      stated limit.
    - An `@id` is an IRI, and not a path, only where it is in the `iri`
      spelling (qro/spelling.py's `IRI`): a scheme of two characters or
      more with no dot, then `:` and something after it. So a drive letter
      (`C:/x`), a stream on a name with a dot (`notes.txt:hidden`) or below
      the crate's top (`data/README:x`), and a bare scheme (`http:`), are
      read as paths, and refused. A stated limit: a stream on a top-level
      name that is itself a scheme (`README:hidden`) reads as an IRI. It is
      then no file the crate holds: no digest may stand on it, and no step
      reads its bytes.
    - Two paths whose names differ only by case are refused, the
      directories along each file and the descriptor's name among them; and
      so is a path that is both a file and a directory (P0.1, after round
      6: `data/A/x` and `data/a/y` were accepted where case is kept). Every
      listed name is held to the exact name on disk, the metadata file's
      among them.
12. **A crate holds no link.** A symbolic link or a junction anywhere in it is
    refused `file-link`, the metadata file among them, so every path stays
    inside the crate on every host. The walk descends in name order, so a
    refusal names the same place on every host.
    So is any entry that is neither a regular file nor a directory, such as
    a named pipe a reader would block on.
13. **Each term names the entities it may stand on** (its domain, in the
    table). A CHECKED term's step checks it on every entity its domain
    admits, and the reader refuses it anywhere else. So no CHECKED field sits
    where no step reads it. A parcel that needs a term elsewhere asks the
    lead, and builds the check with it.
14. **The root is a Dataset, never an action, and carries what every crate
    states:** `conformsTo`,
    `datePublished`, `description`, `hasPart`, `license`, `name`,
    `qro:generator`, `qro:signature`, `qro:trustedTime`, `qro:writer` and
    `qro:writtenAt`.
15. **Text has an alphabet:** no control character but the line feed (C0,
    DEL and C1, Unicode's category Cc), and no lone surrogate. An IRI is
    printable ASCII. A time is a real one, so a leap second's `:60` is
    refused, though RFC 3339 allows it.
16. **Hostile bytes are refused by name, never crash the checker:** a number
    past the parser's reach, nesting past its depth, a NaN, a key twice.
    - A parcel's raw-form reader or generator that fails on a crate is
      refused by its step's name (`raw-form`, `metadata-generated`). So a
      bug in a parcel's reader or generator shows as a refused crate, and
      the refusal's detail names the failure.
    - The command line exits 3 when the checker itself fails, which is never
      a verdict: a crash, or an exit or interrupt raised inside it, in a
      parcel's step or count rule among others, and a parcel's module that
      will not load or registers what is not its own (item 20). A
      `PermissionError` from a step or a count rule is the exception: it is
      misuse, exit 2 (below). A raw-form reader's or a generator's is refused
      by its step's name, as any `Exception` they raise is (above; P0.1's
      verifier, round 1, note 4.3.1). It writes its one line to
      the descriptor
      itself, unbuffered, before it returns. The line is printable ASCII:
      every other character a crate's own text holds, a line feed or an
      escape among them, is written as its Python escape, so no crate can
      break the line or forge another. A verdict it cannot write whole, to a
      closed pipe, a full disk or a closed descriptor, exits 3 (rounds 3 and
      4, R3-1 and R4-1).
    - Two stated limits. A descriptor that takes part of the line and then
      fails has that part, under exit 3. And before the command line runs,
      Python's own failure to start it (no `qro` on the path, a module that
      will not import) exits 1, Python's code, with no line on stdout. So a
      refusal is exit 1 and its REFUSED line.
    - Misuse, exit 2 (round 5, R5-3):
      - an empty name;
      - a crate that is not a directory, or a log or record that is not a
        regular file, a pipe among them;
      - a path the host raises on when asked what it is: a name too
        long, a parent the user cannot search;
      - a path the user may not read or list, the crate's own files and
        directories among them.

      A link to a crate, a log or a record is followed.
17. **P0's fixture** (qro/fixture.py) has its own raw form and generator. The
    command line registers them only with `--fixtures`; the controls and the
    tests do in process. It is every control's twin. It is never a
    provider's form, and the command line run without `--fixtures` refuses a
    crate naming it `step-unbuilt`.
18. **The custody log is JSON lines; the audit record one JSON object.**
    Neither is a crate, so neither is JSON-LD. A log's line is canonical
    compact JSON (sorted keys, no space, ASCII, a final LF). Its `prev` is
    the SHA-256 of the line before, LF included, and the first line's is
    the SHA-256 of the empty string. A log's head is the SHA-256 of its last
    line, or `none` for an empty log. An audit record is canonical JSON with
    an indent of two, like the metadata, and its `logHead` may name any line
    of the auditor's log, so a record pins the log up to the line it names.
    The fields of both are the table's (`CUSTODY_LINE`, `AUDIT_RECORD`), and
    their stated limits are qro/custody.py's.
19. **The canonical bytes are held to golden copies,** tests/format/golden/:
    the twin's metadata and identity, a custody log and its head, and an
    audit record. The writer and the reader share qro/canonical.py, so a
    change to it would move both together; the golden bytes do not move.
20. **A parcel registers its checker code in a module of its own,**
    `qro.register_<parcel>`, so that parcels building at once never edit
    P0's files (P0.1, after its verifier's round 1, D3).
    - The module declares `STEPS`, `RAW_FORMS`, `COUNTS` and `GENERATORS`.
      `checker.load()` merges every parcel's that is present.
    - `load()` refuses a step whose refusals the vocabulary gives another
      parcel, and the vocabulary's sanity check refuses a step given two. It
      refuses a key another function holds, and a name of P0's fixture's,
      with `--fixtures` or without it. It refuses a module that changes the
      registries while `load()` imports it, where it should declare them;
      one imported before that, by a parcel's own test say, it cannot see.
      And a module that raises anything while it is imported or its
      declarations read, a refusal or a want of permission among them, is
      refused, not answered as a verdict (P0.1's verifier, round 2, R2-3).
      Each is the checker's own failure, exit 3.
    - The command line's `check` loads, and so does `python -m
      controls.run`, each before it reads a crate. So an in-process test of
      either loads every parcel present; P0's tests that plant into an
      unbuilt step set the steps unbuilt themselves.
    - A parcel's module is imported on every check, so whatever it imports
      every check needs: a module that will not import fails every check,
      P0's fixture's among them.
    - A parcel's registered code runs on every crate the checker reads, P0's
      fixture and every other parcel's crates among them: a step must
      accept a crate that carries none of its terms.

## Stated limits of P0's format

- **RO-Crate's optional `ro-crate-preview.html`** is refused as
  `file-unlisted`, and so is platform litter such as `.DS_Store`. A crate
  holds only what it lists.
- **The profile's version** is in neither the context nor the profile's
  IRI, so the `context` refusal cannot tell two versions apart. P4, the
  profile, owns that.
- **RO-Crate's `Profile` type** is not in the table yet, so a crate
  describing its profile as a contextual entity is refused `term-unknown`
  until P4 adds it.
- **Process Run Crate's action terms,** `instrument`, `object`, `result`
  and `agent`, are not in the table yet. RO-Crate's context defines them,
  so a `CreateAction` carrying any of them is refused `field-kind` until
  P1, which writes the actions, adds them.
- **What the walk cannot see is not checked.** The checker reads what the
  host lists. A directory it cannot list is raised, never passed over
  (round 5, note 1). The command line answers a want of permission as
  misuse, exit 2, and any other reason, a path too long for the host
  say, as the checker failing, exit 3. These it does not see:
  - an NTFS stream on a listed file is invisible to it, and the file's own
    bytes are held to their digest;
  - a hard link to a file outside the crate is a file in the crate, held
    to its digest like any other;
  - an empty directory holds no file, and is accepted.
- **A path's length is bounded by segment only,** at 255 characters. The
  whole path, the crate's own place on its host included, is not. Where
  Windows' long paths are off, a path past 260 characters cannot be opened
  (round 3, note 6).
