"""A comparison crate's files, its record's form, and the generator step 9 runs on it, `qro-p3-comparison` (P3's design,
items 1, 5 and 7; P3.1). Standard library and qro only.

A COMPARISON is a crate of its own (study QRO-0, section 9):
    comparison/declaration.json        the declaration, qro-comparison/1 (qro.p3_declaration)
    comparison/record.json             the record of its verdicts, qro-comparison-record/1 (below)
    comparison/preregistration/<name>  the copy of the pre-registration the declaration names, any bytes; only then
    ro-crate-metadata.json             generated from the three by `generate`

THE GENERATOR reads the comparison crate's own files and nothing else, never the metadata file: the declaration, read
strictly (one out of its form is a raise, so step 9 refuses the crate `metadata-generated`); the copy of the
pre-registration, exactly the one the declaration names, or none; and the record's digest and size, NEVER ITS CONTENT.
A file it cannot place is a raise. No term of P3's is CHECKED, so the nine steps claim nothing about the record: only
`python -m qro compare`, which re-derives it from the runs' crates, does (qro.p3_compare). The metadata: the
descriptor; the root, its `qro:generator` this one and its `description` saying whether the comparison is declared
real or a rehearsal; the two Profile entities; `#comparison` (a CreateAction and a qro:Comparison: `instrument` the
program, `object` the declaration and the copy, `result` the record, `qro:comparisonKind`, and the header term
`qro:implementation`); `#program-qro-p3`; and the Files, each listed by the root. So "a rehearsal says so in its body"
(section 8) holds: `qro:comparisonKind` and the description are body terms, and step 9 holds both to the declaration.

THE RECORD, `qro-comparison-record/1`: canonical JSON as the metadata (qro.canonical.dumps), every rational in the
profile's spelling, `none` for absence, and no JSON number but a whole count, so every host writes the same bytes. It
is a pure function of the declaration's bytes and the runs' crates' bytes (qro.p3_compare.compute). Its keys:
    alpha, declaration (the declaration file's SHA-256), family (M), format, kind, late (`selector-late` or `none`),
    plan (the plan's digest)
    runs        {"a", "b": {"crates": [{"crate": body digest, "jobs": the selected job ids, sorted, "left": `none`}],
                 "device", "kinds": the selected jobs' devices' kinds, sorted, "question": the question digest}}
    measures    sorted by measure, each {"epsilon", "measure", "refused": `none` or `role-missing`}, a refused one with
                "lacking" (the runs with no member), and one not refused with:
        a, b          {"members": [{"id": the job id, "inScope", "interval": [lower, upper]}], sorted by id,
                       "inScope", "value" (or `none`), "interval", "drift" (U(D), or `none`)}
        difference    [lower, upper], the run a less run b
        means         a word of `means`
        strongForm    a rational, or `none`
        readout       {"status": a word of `status`, "bound": `none` (rho is P3.2's)}
        causes        {"commit", "compile", "device", "drift", "hold", "question", "sampling", "submitted"}
                      (qro.p3_verdicts)
        classes       {"a", "b": {"dephased", "uniform": a word of `class`}}, each run's law's
        statements    words of `statement`, in its order
        unseen        words of `factor`, in its order
"""
import hashlib
import os
from pathlib import Path

from qro import canonical, spelling
from qro import vocabulary as V
from qro.p3_declaration import PREREGISTRATION_DIR, read as read_declaration

GENERATOR = "qro-p3-comparison"
RECORD_FORMAT = "qro-comparison-record/1"
DECLARATION = "comparison/declaration.json"
RECORD = "comparison/record.json"
COMPARISON_ID, PROGRAM_ID = "#comparison", "#program-qro-p3"
PROGRAM = "qro.p3_compare"
IMPLEMENTATION = "qro.p3_compare 0.1.0"
CC_BY = "https://creativecommons.org/licenses/by/4.0/"
DESCRIPTIONS = {"real": "A comparison declared real.",
                "rehearsal": "A comparison declared a rehearsal: never cited as a result."}
HEADER = {"datePublished": "2026-11-08", "qro:writer": "qro, the P3 generator", "qro:writtenAt": "2026-11-08T00:00:00Z",
          "qro:signature": "none", "qro:trustedTime": "none"}


class LayoutError(ValueError):
    """A comparison crate whose files are not the ones its declaration places."""


def dumps(record):
    """The record's canonical bytes."""
    return canonical.dumps(record)


def rational(q):
    return spelling.rational(q)


def pair(bounds):
    return [rational(bounds[0]), rational(bounds[1])]


def _files(crate):
    """Every file of a comparison crate, relative to it, but the metadata file; a link is never followed."""
    crate, out = Path(crate), []
    for dirpath, dirnames, filenames in os.walk(crate, followlinks=False):
        dirnames.sort()
        for n in sorted(filenames):
            rel = Path(dirpath, n).relative_to(crate).as_posix()
            if rel != canonical.DESCRIPTOR:
                out.append(rel)
    return sorted(out)


def _file(crate, rel):
    data = Path(crate).joinpath(*rel.split("/")).read_bytes()
    return {"@id": rel, "@type": "File", "sha256": hashlib.sha256(data).hexdigest(), "contentSize": str(len(data)),
            "encodingFormat": "application/json" if rel.endswith(".json") else "application/octet-stream"}


def generate(crate):
    """The metadata of a comparison crate, from its declaration, its copy of the pre-registration and its record's
    digest and size; LayoutError, or the declaration's own DeclarationError, where its files are not those."""
    crate = Path(crate)
    found = _files(crate)
    if DECLARATION not in found:
        raise LayoutError(f"the comparison crate holds no {DECLARATION}")
    declaration = read_declaration(Path(crate).joinpath(*DECLARATION.split("/")).read_bytes())
    want = {DECLARATION, RECORD} | ({declaration.preregistration} if declaration.preregistration else set())
    extra, missing = sorted(set(found) - want), sorted(want - set(found))
    if missing:
        raise LayoutError(f"the comparison crate lacks {', '.join(missing)}")
    if extra:
        raise LayoutError(f"{extra[0]}: a file of the comparison crate its declaration does not place"
                          + (f" (it names the pre-registration {declaration.preregistration})"
                             if declaration.preregistration and extra[0].startswith(PREREGISTRATION_DIR) else ""))
    files = [_file(crate, rel) for rel in sorted(want)]
    objects = [DECLARATION] + ([declaration.preregistration] if declaration.preregistration else [])
    comparison = {"@id": COMPARISON_ID, "@type": ["CreateAction", "qro:Comparison"],
                  "name": "the comparison of two runs",
                  "instrument": {"@id": PROGRAM_ID}, "object": [{"@id": i} for i in sorted(objects)],
                  "result": [{"@id": RECORD}], "qro:comparisonKind": declaration.plan.kind,
                  "qro:implementation": [IMPLEMENTATION]}
    root = {"@id": canonical.ROOT, "@type": "Dataset", "name": "QRO-Crate P3: a comparison of two runs",
            "description": DESCRIPTIONS[declaration.plan.kind],
            "conformsTo": [{"@id": V.PROCESS_RUN_CRATE}, {"@id": V.PROFILE}], "license": {"@id": CC_BY},
            "hasPart": [{"@id": f["@id"]} for f in files], "mentions": [{"@id": COMPARISON_ID}],
            "qro:generator": GENERATOR, **HEADER}
    program = {"@id": PROGRAM_ID, "@type": "SoftwareApplication", "name": PROGRAM}
    return {"@context": V.context(), "@graph": [V.descriptor(), root, *V.profile_entities(), comparison, program,
                                                *files]}
