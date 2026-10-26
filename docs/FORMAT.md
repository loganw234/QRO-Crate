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
| each spelling's one form | qro/spelling.py; the pattern of each that has one in its `PATTERNS`, for P4's shapes to read |
| the canonical bytes, the body and the crate's identity | qro/canonical.py, its docstring |
| the strict reader's order of decisions (step 1) | qro/reader.py, its docstring |
| the checker's steps 2, 3 and 9, the seam for steps 4 to 8, and its loading of each parcel's registrations (item 20) | qro/checker.py |
| the custody log, the audit record and the custody check | qro/custody.py |
| the controls of section 11 | controls/registry.py, rendered as [CONTROLS.md](CONTROLS.md); each parcel's plants in its own module beside it, merged by `plants()`; which are built, `python -m controls.run` says |

## The choices P0 made

1. **The context is inline:** RO-Crate 1.3's, then one object defining the
   prefix `qro`. A profile term is always written `qro:` and its name, so
   none can collide with, or silently redefine, an RO-Crate term.
2. **The namespace and the profile's IRI are provisional** (question 6).
   The namespace is the generated vocabulary page, each term at its
   anchor, and resolves since the repository is public (question 10). The
   profile's IRI is its description, the README.md that P4 writes in
   profile/; until P4's build is pushed it resolves to nothing (P0.3). GitHub
   lowercases a page's anchors, so a camelCase term's fragment may not land
   on its row, and no two `qro:` names may be equal but for case. Changing
   either IRI is one row of qro/vocabulary.py.
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
   `COUNTS`, which the checker loads (item 20), or re-derives the count in
   its own CHECKED step, as P2's `qro:inScope` is at step 6 (P0.3).
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
      name that is itself a lowercase scheme (`readme:hidden`) reads as an
      IRI (item 22). It is
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
      the refusal's detail names the failure. A `MemoryError` is the
      exception: it is the host's, never a verdict on the crate, so it is
      the checker failing, exit 3 (P1.1's third verifier, D1; P0.7).
    - A parcel's step may itself refuse, by its step's name, what its own
      reading of a crate raises, as P1's steps do. Whatever else a step lets
      through is the checker failing, exit 3, but a `PermissionError`, which
      is misuse, exit 2 (below).
    - The command line exits 3 when the checker itself fails, which is never
      a verdict: a crash, or an exit or interrupt raised inside it, in a
      parcel's step or count rule among others, and a parcel's module that
      will not load or registers what is not its own (item 20). A
      `PermissionError` from a step or a count rule is the exception: it is
      misuse, exit 2 (below). A raw-form reader's or a generator's is refused
      by its step's name, and so is any other `Exception` they raise, a
      `MemoryError` alone excepted (above; P0.1's verifier, round 1, note
      4.3.1). It writes its one line to
      the descriptor
      itself, unbuffered, before it returns. The line is printable ASCII:
      every other character a crate's own text holds, a line feed or an
      escape among them, is written as its Python escape, so no crate can
      break the line or forge another. A line longer than 4,096 characters,
      as escaped, is cut there, where no escape is split, and says how many
      characters it did not write: a hostile file's text, quoted in a
      refusal, put megabytes into one line (P1.1's third verifier, a note;
      P0.7). A verdict it cannot write whole, to a
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
    change to it would move both together; the golden bytes do not. They
    move only with what they hold, in the change that moves it, with its
    reason in the ledger: P0.3's two profile entities moved the twin's three.
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
21. **Each profile the root conformsTo has its contextual entity,** as
    RO-Crate 1.3 requires and the study's section 3 says: exactly its
    `@id`, `@type` `["CreativeWork", "Profile"]`, `name` and `version`, as
    `profile_entities()` in qro/vocabulary.py states them, for this profile
    and for Process Run Crate. The reader holds both at step 1: a missing or
    misshapen one is `graph-form`, and so is a `Profile` entity for no
    profile the root conformsTo; one declaring another version, as text,
    is `context` (P0.3; P4's design, found 1, R3 and D10). The descriptor is
    likewise one function of the table, `descriptor()`.
22. **Every `@id`, and every reference, is one spelling of the IRI it names,**
    so that the graph the checker holds is the graph a JSON-LD reader makes
    (P0.5; P4's verifier, round 1, defect 1). It is one of:
    - `./`, the root;
    - a path in the crate: segments of a file's characters (item 11),
      none empty, `.` or `..`, the first not beginning with `@`, and a
      directory's path ending in `/`. Its last segment, the text after its
      final `/` (empty for a directory), neither ends at its first `;` nor
      begins `.;` or `..;`: `x;`, `;` and `.;x` are refused, and `a;b.txt`,
      `;x` and `x;/` accepted;
    - a fragment, `#` and one or more of RFC 3986's fragment characters,
      holding no `://`;
    - an absolute IRI whose scheme is lowercase, two characters or more
      with no dot, and neither `file` nor a term of the context. A prefix of
      the context, a term whose IRI ends in a gen-delim (`CONTEXT_PREFIXES`
      in qro/vocabulary.py), makes a compact IRI of it to JSON-LD 1.1; any
      term does to JSON-LD 1.0, which RO-Crate 1.3 asks for (P0.5's fourth
      verifier, note 2; P0.7). After its scheme it holds one `#` at most.

    A fragment and an absolute IRI hold RFC 3986's characters but `[` and
    `]`, each `%` beginning an escape of two hex digits. So urllib's
    `urlsplit` reads every accepted id: it raises on a bracket out of place,
    which broke rdflib's `defrag` and its RDF/XML reader given a base
    (P0.5's verifier, round 2, note 4). An IPv6 literal is no host the
    profile needs.

    An entity's `@id` in any other form is refused `spelling`. A
    reference's is refused too: `graph-form` where it is no absolute IRI,
    since no entity's `@id` can then be it (`_:b0`, `./x`), and `spelling`
    where it reads as one (`schema:a`, `HTTPS://x/y`).

    A JSON-LD reader reads many of the other forms otherwise (MEASURED,
    rdflib 7.6.0):
    - `_:b0` is a blank node;
    - `@x`, `.`, `././`, `//` and `?` are the root where the crate is read
      at its directory. Where it is read from its metadata file's own URL,
      `.` and `././` are still the root, and `@x`, `//` and `?` are the
      descriptor's IRI (P0.5's fourth verifier, note 4; P0.7's first
      verifier, D4);
    - `./x` is `x`, `./#a` is `#a`, and `a?` is `a`, its empty query
      dropped;
    - `a//b` and `a/./b` are `a/b`;
    - `/x` and `../a` lie outside the crate, and `//x` is another host;
    - `schema:a` is `http://schema.org/a`; and to a JSON-LD 1.0 processor
      `geo:1,2` is `http://schema.org/geo1,2` (BELIEVED, from 1.0's rule);
    - an absolute `file:` IRI cannot be told from a path;
    - an id holding a space makes no node at all;
    - a fragment holding `://` is left as written, a relative IRI, at every
      base;
    - at a base of a scheme urllib both joins and reads parameters in, of
      which Python 3.12 and 3.13 have eleven (http, https, ftp, sftp, imap, mms, prospero, rtsp, rtsps, rtspu and shttp), a
      `;` in a path's last segment is read as urllib's urljoin reads it, as
      the start of parameters: empty ones are dropped, and a `.` or `..`
      before them is read as a dot segment. So `x;` is `x`, and `;` the base
      itself: the root where the crate is read at its directory, and the
      descriptor's IRI where it is read from its metadata file's own URL
      (P0.5's verifiers, rounds 1 and 3; P0.7's first verifier, D4).

    Others rdflib reads as written (`x#a`, `#`, `?q`, `HTTPS://x/y`, `C:/x`,
    `ab:%zz`). They are refused as forms the rule does not offer, so that an
    IRI has one spelling: the profile names nothing inside a file and no
    query, and writes a scheme in lowercase. One spelling is as RDF compares
    IRIs, character for character: the rule normalises nothing, so `%2F` and
    `%2f`, or `a` and `%61`, are two IRIs, each its own spelling.

    So distinct `@id`s name distinct IRIs, as JSON-LD 1.1 reads them, a
    relative id resolved by RFC 3986's algorithm and an absolute IRI kept as
    written, and as rdflib 7.6.0 does (MEASURED after P0.5's second round
    under Python 3.12.9, and after its third under 3.13.5, every reading the
    same: 300,000 ids drawn under the rule, at nine bases. At the eight
    whose path is hierarchical, `file:`, `http:`, `https:` and `ftp:` among
    them, each was read as JSON-LD 1.1 reads it, and no two the same. At a
    `urn:` base rdflib joins an id onto the URN's own path instead, and no
    two the same there either). By RFC 3986's algorithm alone, two absolute
    IRIs that differ only by a dot segment would be one,
    `http://example.org/a/../b` and `http://example.org/b`; JSON-LD 1.1 and
    rdflib keep each as written. tests/format/test_spelling.py holds the
    rule to a model of rdflib's reading, which made the same IRI as rdflib
    of every one of those ids. Four stated limits:
    - an absolute IRI equal to the IRI a relative id resolves to where the
      crate is read is one node with that id there, a path's, a fragment's
      or the root's. Two examples, for a crate read at
      `https://example.org/crate/`: `https://example.org/crate/x` with the
      path `x`; and, for a crate read from its metadata file's own URL,
      `https://example.org/crate/ro-crate-metadata.json#a` with `#a`;
    - an absolute IRI and a fragment are held to their characters, their
      escapes and one `#`, not to the rest of RFC 3986's grammar.
      `http://a:b:c/`, a port of letters, is accepted. rdflib keeps it as
      written; a processor that converts only well-formed IRIs drops it
      (P0.5's verifiers, rounds 1 and 2, notes);
    - rdflib departs from JSON-LD 1.1 at some bases, though at none it was
      measured at does it make one node of two accepted ids, but as the
      first limit says. At a base of a scheme urllib does not join
      (`mailto:`, `s3:`, `data:`), it makes no node of a relative id, but of
      a fragment holding `:`, which it leaves the relative IRI `.#a:b`. At a
      base with an empty path (`https://example.org`), it reads `#a` as
      `https://example.org/.#a`. And from a base's own path it collapses a
      `//`, removes dot segments, and drops a final `;` for a fragment, and
      it writes the base's scheme in lowercase (P0.5's verifiers, rounds 2
      to 4);
    - a JSON-LD 1.0 processor makes a prefix of every term of the context,
      and RO-Crate 1.3 asks for JSON-LD 1.0, so an absolute IRI whose scheme
      is any term is refused (P0.7). That a 1.0 processor reads one as
      another IRI is BELIEVED, from 1.0's rule; none was run, and rdflib
      reads 1.1's rule even when told 1.0. The rule has a cost. Of
      RO-Crate 1.3's 3,069 terms, 333 have a scheme's shape. Six of them are
      schemes IANA registers (fetched 2026-10-25): `about`, `data` and
      `geo`, permanent, and `maps`, `query` and `tool`, provisional. An IRI
      of those schemes, a `data:` or a `geo:` IRI say, is refused though
      it names no term (MEASURED, against the pinned context).

## Stated limits of P0's format

- **RO-Crate's optional `ro-crate-preview.html`** is refused as
  `file-unlisted`, and so is platform litter such as `.DS_Store`. A crate
  holds only what it lists.
- **The profile's version is held in the graph,** by each profile's
  contextual entity, and in neither the context nor the namespace: a term
  keeps one IRI across versions, and a changed meaning is a new term. The
  reader reads exactly one version of each profile (P0.3).
- **Process Run Crate's `agent`** is not in the table yet. RO-Crate's
  context defines it, so a `CreateAction` carrying it is refused
  `field-kind`. P1's design added `instrument`, `object` and `result`
  (P0.3).
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
