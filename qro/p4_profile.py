"""The Profile Crate and everything in profile/ that is generated (P4's design, items 1 to 3).

`render()` is one pure function from the vocabulary table, RO-Crate's pinned context and P0's profile/context.jsonld to
`{path relative to profile/: bytes}`: the Profile Crate's metadata, the description the profile IRI resolves to, the
matrix of examples, a rocrate-validator profile, the shapes, and a copy of P0's fixture crate. tools/gen_profile.py
writes it and refuses drift. Nothing in the output is read from a clock, a path, a user or a host, so two renders
are the same bytes anywhere. Every file is ASCII with LF line ends.

The Profile Crate is an RO-Crate 1.3 Profile Crate, and `check_profile_crate` holds it to the rules of the specification's
profiles page that its bytes show, which its docstring lists; what it does not hold is stated as limits (README limits 9, 11,
17 and 22). That is P4's own check, not RO-Crate's validator's, and it is not the QRO checker either: a Profile Crate is not
a QRO crate and nothing in this repository reads one with the strict reader. Stdlib only.
"""
import hashlib
import json
import tempfile
from pathlib import Path

from qro import canonical, checker, fixture
from qro import spelling as S
from qro import vocabulary as V
from qro.p4_examples import FAMILIES, PLANTS, generated, matrix_rows
from qro.p4_shapes import FILES, groups, level_of, prefixes
from qro.p4_shapes import problems as shape_problems
from qro.p4_turtle import render as render_turtle

REPO = Path(__file__).resolve().parent.parent
CONTEXT = "context.jsonld"                  # P0's, written by tools/gen_vocabulary.py: read here, never written
# The raw URL the generator writes. A permanent IRI is two edits (V.PROFILE, V.NAMESPACE) and this one (P4's design,
# item 2); at a release the redirect targets are a tag's, not main's.
RAW_HOME = "https://raw.githubusercontent.com/loganw234/QRO-Crate/main/"
# The profile's JSON-LD context at its absolute IRI: RO-Crate 1.3 asks the entity that represents a context to have one
# (provisional, like the profile's own: limit 11).
CONTEXT_IRI = RAW_HOME + "profile/" + CONTEXT
JSONLD_CONTEXT = "http://www.w3.org/ns/json-ld#Context"       # what a JSON-LD context conforms to
JSONLD_FORMAT = "application/ld+json"
DATE_PUBLISHED = "2026-10-16"               # the build's day; the lead sets it at release (P4's design, D7), never a clock
LICENSE = "https://creativecommons.org/licenses/by/4.0/"
ROLE = "http://www.w3.org/ns/dx/prof/role/"
ROLES = ("constraints", "example", "guidance", "mapping", "schema", "specification", "validation", "vocabulary")
DCT_CONFORMS = "http://purl.org/dc/terms/conformsTo"
CONTEXT_URL = V.ROCRATE_CONTEXT
TOKEN = "qro-crate"                         # the rocrate-validator profile's token and directory
VALIDATOR = f"validator/{TOKEN}/"
MEDIA = {".md": "text/markdown", ".ttl": "text/turtle", ".json": "application/json",
         ".jsonld": "application/ld+json", ".txt": "text/plain"}
DESCRIPTION = "README.md"
EXAMPLES = "EXAMPLES.md"
FIXTURE_DIR = "examples/fixture/"
# What pyshacl 0.40.1 makes of these shapes when it is told to infer: the results it gives for the accepted fixture crate
# under each mode but `none`, which gives none (limit 2). MEASURED by P4's fourth verifier, and held by the engine stage
# (tests/p4shacl/test_p4shacl_inference.py), so that the counts the README and the Turtle banner quote are the engine's.
INFERENCE = {"rdfs": 94, "owlrl": 112, "both": 527}
INFERENCE_COUNTS = f"{INFERENCE['rdfs']}, {INFERENCE['owlrl']} and {INFERENCE['both']}"
INFERENCE_SHAPES = ("descriptor", "entity", "profile-entities")         # the must shapes it fails, in each of the three modes
INFERENCE_NAMES = ", ".join(INFERENCE_SHAPES[:-1]) + f" and {INFERENCE_SHAPES[-1]}"
INFERENCE_CODE = ", ".join(f"`{s}`" for s in INFERENCE_SHAPES[:-1]) + f" and `{INFERENCE_SHAPES[-1]}`"       # as markdown


class ContextMissing(RuntimeError):
    """P0's profile/context.jsonld is not a file this can read (not there, a link, a directory): the message says which, and
    that tools/gen_vocabulary.py --write makes it. Its text is a whole sentence, which the tool writes as it is."""


def sha(data):
    return hashlib.sha256(data).hexdigest()


def ascii_md(text):
    """Markdown in ASCII: every other character as a numeric character reference, which GitHub renders."""
    return "".join(c if ord(c) < 0x80 else f"&#{ord(c)};" for c in text)


def cell(s):
    return str(s).replace("|", "\\|").replace("\n", " ")


def local_id(shape):
    return shape.id.split("#", 1)[1]


# -- the stated limits: the one place they are written (the README renders them; docs/P4.md points at them) -----------
LIMITS = (
    ("The checker is the authority.",
     "A shape is a consequence of what the checker holds. Tests hold two things, and the second is narrower. When a must "
     "shape fails, the checker refuses the crate (steps 1 to 3): over every plant, a seeded fuzz and every one of the "
     "12,591 single edits of the fixture that the first verifier's pool makes. When a crate is one fault away from one the "
     "checker accepts, it is refused by a name that a failing shape claims: over the same edits, 124 crates with a key "
     "spelt another way, and 469 crates of three families the second verifier found and the pool never made "
     "(an @id added again with a term of its own, or a path the reader holds as another's; a top-level @context or key of "
     "the crate's own; a File added whose file the disk lacks, or a link). Every must shape claims, beside the refusals it "
     "mirrors, the six of steps 1 and 2 that can come before its own and that RDF cannot show: `spelling`, "
     "`term-unknown`, `graph-form`, `context`, `file-missing` and `file-link`. Each is seen needed: with it left out, "
     "the sweeps find a crate on which a must shape fails and the checker's refusal is claimed by no failing shape "
     "(`context` through a real engine, which reads the crate's own context where the evaluator abstains; `file-link`, "
     "claimed from reading the checker's walk, by a File added at the path of a link, which is a junction on Windows, "
     "where no privilege is needed, and a symbolic link elsewhere). A crate with several faults is refused too, but its "
     "first refusal can be a fault no failing shape mirrors, and then its name is not claimed. A crate the expansion cannot read, one with an id the reader refuses or "
     "a context of its own, is never left out of these: the evaluator abstains from it, the checker has refused it, and "
     "the engine stage reads the contexts through a real engine. A walk over every crate plant of any parcel whose "
     "control row says it is accepted is written; none is built yet (the one accepted is a custody log), so it has "
     "examined no crate. These are samples, not proofs; limit 19 says what is held of ids, and at which base. What the "
     "shapes do not say is the checker's alone."),
    ("The shapes are held to one engine, and to an evaluator of this repository's.",
     "A real engine, pyshacl 0.40.1 on rdflib 7.6.0, reads the Turtle in the engine stage, which runs only where one is "
     "named (QRO_SHACL_PYTHON), and the quick budget's gates read the same shapes as data with an in-process evaluator. "
     "A construct the micro cases and the per-crate comparison do not hold is held by neither, and another engine may "
     "read a construct differently (limit 23 names three things on which the evaluator and pyshacl differ). Regular "
     "expressions are Python's `re` in both; they are written in the syntax an XPath engine shares, and no other engine "
     "was run. The shapes are for an engine run without inference: pyshacl's `inference` is `none`, its default, in the "
     "engine stage and wherever these shapes are used. With `rdfs`, `owlrl` or `both` it fails the accepted fixture crate "
     f"on {INFERENCE_CODE}, with {INFERENCE_COUNTS} results, because the shapes judge the graph a crate says and an "
     "inference adds triples to it: types that their lists of types do not allow (`rdfs:Resource` and `rdf:Property`; "
     "with OWL-RL `owl:Thing`, `rdfs:Datatype` and others) and self-triples that their closed shapes do not allow "
     "(`rdfs:subPropertyOf`; with OWL-RL `owl:sameAs`, `rdfs:subClassOf` and others). MEASURED: the counts by P4's fourth "
     "verifier and again by the engine stage, which holds them; the types and self-triples by one run of P4's fifth-round "
     "builder over the results' paths and values, which no test holds."),
    ("Some spellings are looser in a shape than in the checker.",
     "A size above 2^63 - 1 or with a trailing line feed; a rational not in lowest terms, with a term of more than "
     "1,000 digits, or with a trailing line feed; a binary64 whose decimal is not the bits' exact one, or with a "
     "trailing line feed; a time that is not real (30 February, :60, T24:00) or with a trailing line feed; a date that "
     "is not real (month 13, 30 February); an iri with a trailing line feed; a text with a control character, a lone "
     "surrogate or a trailing line feed. A pattern holds a form, not that a date is real, a fraction reduced or a "
     "decimal exact. The trailing line feed is Python's `re`, where `$` matches before a final line feed; a SPARQL "
     "engine may not allow it (BELIEVED, not re-read)."),
    ("A `local-file` is read as any `File`, and the digest rule is for `file:` IRIs.",
     "`domain-sha256` and `domain-contentsize` admit any File, and `file-digest-present` asks a digest of a File whose "
     "IRI is a `file:` IRI with no `#`, which is what a relative id resolves to against the evaluator's base. A File "
     "with another absolute IRI (`https:`, `urn:`) is exempt, as the checker exempts it, and read from a base that is "
     "not `file:`, no File is judged. A File whose id is itself an absolute `file:` IRI would be asked a digest by a real "
     "engine, which reads it as a path in the crate, and the checker asks none (MEASURED, the plant "
     "`abstains-absolute-file-id`). The reader refuses such an id `spelling` (FORMAT.md item 22), so no accepted crate "
     "has one, and the evaluator abstains from the crate (limit 19). A remote File, an absolute IRI that is no path in "
     "the crate, carrying a sha256 is refused `graph-form` by the checker, whether or not the root lists it, since "
     "sha256 stands only on a File the crate holds; the shapes read it as any File, so it conforms where the root "
     "lists it in `hasPart`, and fails `file-reached` where the root does not, a shape that claims `graph-form` "
     "(MEASURED, listed and unlisted, with and without a contentSize)."),
    ("A key no context defines never reaches RDF.",
     "JSON-LD drops it, so a crate with `madeUp` conforms to the shapes and is refused `term-unknown`. A key RO-Crate's "
     "context spells another way (`schema:name` or the absolute IRI, for `name`) reaches RDF as the table's own term. "
     "The checker refuses it `term-unknown` (`graph-form` on the descriptor and on a contextual Profile entity, whose "
     "keys it holds one by one), whatever the shapes say: they may conform (a valid value, on an entity that has none) "
     "or fail (a second `name`, a value in no spelling, a term where its domain does not admit it), and when they fail "
     "a failing shape claims the refusal (every must shape claims `term-unknown`). A type spelt another way "
     "(`MediaObject` for `File`, `schema:Dataset`) is the same."),
    ("One value and a one-element list, the order of a list, of the graph and of a type list are invisible to RDF.",
     "A `name` written as a list of one, and a `hasPart` out of order, conform to the shapes and are refused "
     "`spelling`. An empty list makes no triple: `license: []` fails the root's shape for a missing license, and the "
     "checker refuses the form, `spelling`, which every must shape claims."),
    ("Bytes, files, counts and every re-derivation are the checker's alone.",
     "A moved shot, a digest that is not its file's, a stated count one too high and an adjusted count conform to every "
     "shape and are refused `raw-digest`, `file-digest`, `count-unpaid` and `raw-form`. So is everything steps 4 to 9 "
     "re-derive."),
    ("`should/` holds rule 2's absence shapes, and `may/` is empty.",
     "Nothing in the format is an optional behaviour a shape can state. Recommended practice is checked only by "
     "rule 2's absence rule, as a Warning."),
    ("The Profile Crate is held by this repository's own check, not by RO-Crate's validator.",
     "`check_profile_crate` holds the MUSTs of RO-Crate 1.3's profiles page that bytes show (the root typed Dataset and "
     "Profile, the human-readable description a File about the root that `hasPart` lists, a contextual Profile entity "
     "for every profile the root is a profile of, and for an entity that conforms to JSON-LD's Context an absolute "
     "`@id` and the encodingFormat `application/ld+json`), the SHOULDs its docstring lists (the root's absolute `@id`, "
     "name, `isProfileOf` and `hasPart`; for each resource a role, an artifact, and on each artifact an "
     "`encodingFormat`) and the core's. It holds no more: limits 11, 17 and 22 state the SHOULDs not met. Its root `@id` "
     "is an absolute IRI, as RO-Crate's examples have it; rocrate-validator's rule that a root data entity's URI end "
     "with a slash may refuse that (BELIEVED, not run)."),
    ("rocrate-validator 0.12.2 was not run on these shapes, and cannot check Process Run Crate 0.6.",
     "Its Process Run Crate profile is 0.5, and the types its ontology infers may trip the closed shape. Its folder "
     "layout is followed as read, not as run."),
    ("The profile's IRIs are provisional.",
     "The profile IRI is this page, and no machine-readable Profile Crate is served from it; GitHub lowercases a page's "
     "anchors, so a camelCase term's fragment lands on its row only by luck. A tool that follows RO-Crate's retrieval "
     "order finds no Profile Crate from the IRI. The entity that represents the JSON-LD context has, as the absolute "
     "`@id` RO-Crate 1.3 asks, the raw GitHub URL of context.jsonld on main. RO-Crate asks it to be retrievable as "
     "JSON-LD, a permalink and versioned: this one moves with the branch, and the host is believed to serve the file as "
     "`text/plain` (BELIEVED, not fetched). The profile's `identifier` is not set, since it is for a permanent IRI. At "
     "the switch to a permanent IRI the entity is regenerated with the rest."),
    ("A crate under a provisional IRI is a different crate from the same crate under a permanent one.",
     "The identity digest covers both IRIs, and a custody log names digests, so no crate is to be published or "
     "archived under a provisional IRI, and at the switch every generated file and every crate is regenerated, never "
     "edited."),
    ("One version at a time.",
     "The checker, the reader and these shapes read this version. A crate declaring another is refused `context`; "
     "reading two would need two tables chosen by the declared version."),
    ("The fixture needs `--fixtures`.",
     "P0's fixture has its own raw form and generator, which only the checker's `--fixtures` registers, so the plain "
     "command line refuses the example `step-unbuilt`, by design."),
    ("The matrix lists only this profile's own plants.",
     "Another parcel's crate plants are held to the shapes' soundness, and are not described here."),
    ("Presence rules are this profile's own, until the table says where a term is required.",
     "A presence rule a later step adds is not a must shape until someone writes the line: the shapes are then weaker "
     "than the checker, never stricter."),
    ("The levels of the study's section 9 are not expressed by any shape.",
     "Recorded, anchored, comparable and quantum-comparable are properties of a comparison, not of a crate's graph. "
     "The description file's media type is `text/markdown`, where RO-Crate asks `text/html`."),
    ("A report's `sh:conforms` is false for a Warning or an Info too.",
     "That is the Recommendation. A user who runs an engine on a crate with only should-level results sees \"does not "
     "conform\" and filters by severity."),
    ("An id is read at one base, as FORMAT.md item 22 admits it, and item 22's own limits pass to the shapes.",
     "The reader admits an @id, and a reference's, in four forms only: the root, a path in the crate, a fragment, and an "
     "absolute IRI whose scheme is lowercase and neither `file` nor a prefix of the context. For every id it accepts the "
     "expansion makes the IRI rdflib 7.6.0 makes, at the base `file:///crate/`, and distinct ids are distinct IRIs: held "
     "by the engine stage over tens of thousands of ids drawn from the four forms and from every short string of the "
     "characters that bite, and by the quick stage's gates on the expansion's side. The ids the reader refuses and a "
     "JSON-LD reader reads otherwise (`_:b0` as a blank node, `@x` as the root, `a//b` as `a/b`, `//x` as another host, a "
     "`file:` IRI as a path) the expansion refuses to read where it knows rdflib's reading, and the evaluator then "
     "abstains. That is harmless, since the checker has refused the crate and no gate skips one. A real engine reads "
     "such a crate its own way and may fail a shape the evaluator never sees (`entity` on `_:b0`, `term-name` on `@x`, "
     "`file-digest-present` on an absolute `file:` id, `term-haspart` on a reference to `_:b0`: the plants of the family "
     "`abstains`, MEASURED, pyshacl 0.40.1), on a crate the checker refused first, by a name the failing shape claims: "
     "the checker refuses an id outside the rule `spelling`, and a reference outside it `graph-form`, and every must "
     "shape claims both. What stays is item 22's own, and it binds the shapes. A crate read where it "
     "lives is read at another base, and an absolute IRI equal to the IRI a relative id resolves to is one node with "
     "it (`https://example.org/crate/x` beside the path `x`, read at `https://example.org/crate/`): a term shape can "
     "then fail on two entities the checker holds apart, and at `file:///crate/` no such IRI is an id. An absolute IRI "
     "and a fragment are held to their characters, not to the rest of RFC 3986's grammar (`http://a:b:c/`), which a "
     "processor that converts only well-formed IRIs drops. rdflib departs from JSON-LD 1.1 at a base urllib does not "
     "join (`mailto:`, `s3:`, `data:`) and at one with an empty path. A JSON-LD 1.0 processor makes a prefix of every "
     "term of the context, and RO-Crate 1.3 names no version, so to such a processor an absolute IRI whose scheme is a "
     "term (`geo:x`, `name:x`) is another IRI (BELIEVED, from 1.0's rule; none was run)."),
    ("A graph with no descriptor or no root has nothing for those shapes to judge.",
     "The descriptor and root shapes have the descriptor and what it is about for focus nodes; the checker refuses a "
     "crate without them `graph-form`."),
    ("A name RO-Crate's context gives a listed type passes the type check.",
     "`MediaObject` is `File` in RDF, so a type written `MediaObject` conforms and is refused `term-unknown`."),
    ("The extension terms are mapped by one prefix, not each by its code.",
     "RO-Crate 1.3 asks the `termCode` of a DefinedTerm to be valid as a key in a conforming crate's context, and the term "
     "to be mapped to its `@id` in the Profile Crate's `@context`. The Profile Crate's `@context` maps the one prefix a QRO "
     "crate's maps, `qro`, so that every `qro:code` is its DefinedTerm's `@id`. The codes are not mapped as bare keys: QRO "
     "crates write `qro:code`, and some codes (`device`, `line`, `value` and `Question` today) are terms of RO-Crate's own "
     "context, which a mapping in the Profile Crate would redefine. That SHOULD is not met."),
    ("The evaluator and pyshacl read three things differently, and none changes a verdict on a crate.",
     "`sh:minLength 0` on a blank node: the evaluator fails it, since a blank node has no string to measure (READ, the "
     "Recommendation's section 4.4.1, in an extraction), and pyshacl 0.40.1 does not. `sh:maxInclusive` with no "
     "`sh:minInclusive`, against a boolean literal: the evaluator fails it, since a boolean has no order with a number, "
     "and pyshacl 0.40.1 passes it (BELIEVED the evaluator is right, from SPARQL's comparison rules; not re-read). "
     "MEASURED by 28,000 random shapes over random graphs, through the engine stage's runner (P4's second verifier): "
     "these were the only disagreements, in 16 cases and 2. The generated shapes use neither: no `sh:minLength` is "
     "below 1 (`sh:maxLength` is used, with several bounds, and the two read it alike), and no `sh:maxInclusive` "
     "stands without its `sh:minInclusive`; a test holds that, and the engine stage holds the two "
     "disagreements as they are, so that a new engine is noticed. A shape written with either would be read two ways, "
     "and its micro case would have to say which. The third is the lexical form of an integer. The generated shapes do "
     "use `sh:datatype xsd:integer` (three terms), and on a literal whose lexical form Python's `int()` reads and XSD's "
     "lexical space may not (`' 1'`, `'1 '`, a tab and a line feed around `1`, `'1_0'`, U+0661 and U+FF11, and others of "
     "their kinds: other white space, an underscore between digits, the digits of other scripts) the evaluator fails the "
     "shape, as for an ill-formed literal, and pyshacl accepts the literal, because rdflib 7.6.0 maps an integer's lexical "
     "form with Python's `int()` and calls a literal well formed when it has a value (READ, rdflib/term.py in the pinned "
     "environment; MEASURED by P4's fourth verifier and again in the engine stage, which holds the six forms as they are "
     "and their neighbours, where the two agree). No crate reaches these forms. The reader takes an integer only as a "
     "JSON number in its one spelling and refuses any other `spelling`, and the expansion writes a number as its decimal "
     "digits alone (held in the quick stage), so the soundness of the shapes is untouched. What the tree can say of which "
     "judge is right: the checker refuses all six forms, so pyshacl's reading is the looser, which is the safe direction "
     "and no claim of more than the checker holds, and the evaluator's agrees with the checker's. What it cannot say: "
     "which is right by XSD 1.1 and RDF 1.1 Concepts, since it pins no copy of either. BELIEVED, from XSD 1.1's "
     "definition of the integer, recalled and not re-read: its lexical space is an optional sign and ASCII digits, so "
     "the evaluator is right on `'1_0'` and on the two digits; on the three forms with white space it turns on whether "
     "XSD's collapse of white space applies to an RDF literal's lexical form, which is not settled here."),
)


# -- the Turtle ------------------------------------------------------------------------------------------------------
def banner(path, shapes):
    level = level_of(path)
    return ["GENERATED by tools/gen_profile.py from qro/vocabulary.py. Edit the definition and run --write; never this file.",
            f"QRO-Crate {V.PROFILE_VERSION}: {len(shapes)} {level}-level shapes in SHACL Core (no SPARQL).",
            "The checker (python -m qro check) is the authority. A shape is a consequence of it. qs:claims names the",
            "refusals it mirrors, then the six of steps 1 and 2 that can come before its own: spelling, term-unknown,",
            "graph-form, context, file-missing, file-link. When a must shape fails the checker refuses the crate; a crate",
            "one fault from an accepted one is refused by a name a failing shape claims (README, limit 1).",
            "A report's sh:conforms is false for a Warning too; filter by sh:resultSeverity.",
            "Run an engine WITHOUT inference (pyshacl: inference=none, its default). With rdfs, owlrl or both it fails the",
            f"accepted fixture crate on {INFERENCE_NAMES}, with {INFERENCE_COUNTS} results (README, limit 2)."]


def shapes_files():
    """{path under profile/: bytes}: the shapes as Turtle, one file a folder's group, in the rocrate-validator layout."""
    return {VALIDATOR + path: render_turtle(shapes, prefixes(), banner(path, shapes)).encode("ascii")
            for path, shapes in groups().items()}


def profile_ttl():
    """The rocrate-validator profile: this profile, which is a profile of RO-Crate 1.3, and its token. The layout
    follows what was read of rocrate-validator 0.12.2; no validator has read it."""
    lines = ["# GENERATED by tools/gen_profile.py from qro/vocabulary.py. Edit the definition and run --write.",
             "@prefix prof: <http://www.w3.org/ns/dx/prof/> .",
             "@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .", "",
             f"<{V.PROFILE}> a prof:Profile ;",
             f'    rdfs:label "QRO-Crate {V.PROFILE_VERSION}" ;',
             '    rdfs:comment "An RO-Crate profile for quantum runs. Its shapes are SHACL Core; the checker is the '
             'authority, and the shapes are a consequence of it." ;',
             f"    prof:isProfileOf <{V.ROCRATE}> ;", f'    prof:hasToken "{TOKEN}" .', ""]
    return "\n".join(lines).encode("ascii")


# -- the fixture's copy ----------------------------------------------------------------------------------------------
def fixture_files():
    """P0's fixture crate, built now in a temporary directory: {path under profile/examples/fixture/: bytes}."""
    with tempfile.TemporaryDirectory() as d:
        crate = fixture.make(Path(d) / "crate")
        return {FIXTURE_DIR + p.relative_to(crate).as_posix(): p.read_bytes() for p in sorted(crate.rglob("*"))
                if p.is_file()}


# -- the Profile Crate's metadata --------------------------------------------------------------------------------------
SHAPE_TEXT = {"1_structure": "the graph's structure", "2_terms": "a shape for each term's one spelling",
              "3_domains": "a shape for each term's domain", "1_absence": "rule 2, absence written as a word"}
FILE_TEXT = {
    DESCRIPTION: "The profile description: what the profile is, how a crate declares it, what the shapes hold and cannot "
                 "see.",
    EXAMPLES: "The matrix of examples: what the checker and the shapes each say of every example and plant.",
    CONTEXT: "The JSON-LD context a QRO crate inlines after RO-Crate 1.3's; P0's file, generated from the vocabulary.",
    VALIDATOR + "profile.ttl": "The rocrate-validator profile description.",
    FIXTURE_DIR + "ro-crate-metadata.json": "The fixture crate's metadata.",
    FIXTURE_DIR + "data/notes.txt": "A note the fixture lists.",
    FIXTURE_DIR + "data/raw.counts.json": "The fixture's raw result.",
}
for _path in FILES:
    FILE_TEXT[VALIDATOR + _path] = (f"{level_of(_path).capitalize()}-level shapes: {SHAPE_TEXT[Path(_path).stem]}.")


def file_entity(path, data):
    e = {"@id": path, "@type": "File", "name": path, "description": FILE_TEXT[path],
         "encodingFormat": MEDIA[Path(path).suffix], "contentSize": str(len(data)), "sha256": sha(data)}
    if path == CONTEXT:
        e["sameAs"] = ref(CONTEXT_IRI)            # this copy of the context is the document at its absolute IRI
    return e


def qro_terms():
    """[(key, meaning)] of every `qro:` term and type of the table."""
    return [(key, meaning) for key, meaning in [(t.key, t.meaning) for t in V.TERMS] + [(y.key, y.meaning) for y in V.TYPES]
            if key.startswith(V.PREFIX + ":")]


def defined_term_ids():
    """The @ids the vocabulary's DefinedTerms have: the namespace and the term's code."""
    return {V.NAMESPACE + key[len(V.PREFIX) + 1:] for key, _ in qro_terms()}


def defined_terms():
    """The vocabulary as an extension vocabulary of the Profile Crate (RO-Crate's convention): a DefinedTerm a qro: term
    and type, from the table, so that the vocabulary is written once."""
    return [{"@id": V.NAMESPACE + key[len(V.PREFIX) + 1:], "@type": "DefinedTerm", "name": key,
             "termCode": key[len(V.PREFIX) + 1:], "description": meaning, "inDefinedTermSet": {"@id": V.NAMESPACE}}
            for key, meaning in qro_terms()]


def ref(i):
    return {"@id": i}


def metadata(files, context_bytes):
    """The Profile Crate's ro-crate-metadata.json, as a dict, for `files` (the rendered files but this one) and P0's
    context. Its entities in the order the QRO writer uses: the descriptor, the root, then by @id."""
    validator = sorted(p for p in files if p.startswith(VALIDATOR))
    example = sorted(p for p in files if p.startswith(FIXTURE_DIR))
    data = {**files, CONTEXT: context_bytes}
    entities = {p: file_entity(p, data[p]) for p in sorted(data)}
    # The recommended profile's page is HTML (its IRI answers a redirect to one: READ 2026-10-15); an artifact of a
    # resource descriptor declares its encodingFormat (RO-Crate 1.3, profiles page).
    prc = dict(next(e for e in V.profile_entities() if e["@id"] == V.PROCESS_RUN_CRATE), encodingFormat="text/html")

    def refs(*ids):
        return sorted([ref(i) for i in ids], key=canonical.sort_key)
    graph = [
        {"@id": canonical.DESCRIPTOR, "@type": "CreativeWork", "about": ref(V.PROFILE), "conformsTo": ref(V.ROCRATE)},
        {"@id": V.PROFILE, "@type": ["Dataset", "Profile"], "name": V.PROFILE_NAME,
         "description": "An RO-Crate profile for quantum runs, and the checker that holds a crate to it. This is the "
                        "profile's own crate: its description, vocabulary and context, its SHACL shapes, and its examples.",
         "version": V.PROFILE_VERSION, "datePublished": DATE_PUBLISHED, "license": ref(LICENSE),
         "isProfileOf": ref(V.ROCRATE),
         "hasPart": sorted([ref(DESCRIPTION), ref(EXAMPLES), ref(CONTEXT), ref(VALIDATOR), ref(FIXTURE_DIR)],
                           key=canonical.sort_key),
         "hasResource": sorted([ref(f"#{n}") for n in ("hasContext", "hasExamples", "hasShapes", "hasSpecification",
                                                       "hasVocabulary", "shouldConformToProcessRun")],
                               key=canonical.sort_key)},
        {"@id": "#hasSpecification", "@type": "ResourceDescriptor", "hasRole": ref(ROLE + "specification"),
         "hasArtifact": ref(DESCRIPTION)},
        {"@id": "#hasContext", "@type": "ResourceDescriptor", "hasRole": ref(ROLE + "vocabulary"),
         "hasArtifact": ref(CONTEXT_IRI)},
        {"@id": "#hasVocabulary", "@type": "ResourceDescriptor", "hasRole": ref(ROLE + "vocabulary"),
         "hasArtifact": ref(V.NAMESPACE)},
        {"@id": "#hasShapes", "@type": "ResourceDescriptor", "hasRole": ref(ROLE + "validation"),
         "hasArtifact": refs(*validator)},
        {"@id": "#hasExamples", "@type": "ResourceDescriptor", "hasRole": ref(ROLE + "example"),
         "hasArtifact": refs(EXAMPLES, *example)},
        {"@id": "#shouldConformToProcessRun", "@type": "ResourceDescriptor", "hasRole": ref(DCT_CONFORMS),
         "hasArtifact": ref(V.PROCESS_RUN_CRATE)},
        {"@id": V.ROCRATE, "@type": ["CreativeWork", "Profile"], "name": "RO-Crate Metadata Specification",
         "version": V.ROCRATE.rsplit("/", 1)[1]},
        prc,
        {"@id": LICENSE, "@type": "CreativeWork", "name": "CC BY 4.0",
         "description": "Creative Commons Attribution 4.0 International"},
        {"@id": V.NAMESPACE, "@type": "DefinedTermSet", "name": "the QRO-Crate vocabulary",
         "url": V.NAMESPACE.rstrip("#"), "encodingFormat": "text/html"},
        {"@id": CONTEXT_IRI, "@type": "CreativeWork", "name": "the QRO-Crate JSON-LD context",
         "description": "The context a QRO crate inlines after RO-Crate 1.3's: it maps the prefix qro to the vocabulary's "
                        "namespace. The copy in this crate is context.jsonld. Its IRI is provisional (limit 11).",
         "encodingFormat": JSONLD_FORMAT, "conformsTo": ref(JSONLD_CONTEXT), "version": V.PROFILE_VERSION},
        {"@id": JSONLD_CONTEXT, "@type": "DefinedTerm", "name": "JSON-LD Context", "url": "https://www.w3.org/TR/json-ld/"},
        {"@id": VALIDATOR, "@type": "Dataset", "name": "the shapes as a rocrate-validator profile",
         "description": "The profile's SHACL Core shapes in the layout rocrate-validator reads: a profile description "
                        "and a folder for each requirement level.",
         "hasPart": [ref(p) for p in validator]},
        {"@id": FIXTURE_DIR, "@type": "Dataset", "name": "P0's fixture crate",
         "description": "The smallest crate every one of P0's checker steps reads: the positive example. The checker "
                        "accepts it with --fixtures.",
         "hasPart": [ref(p) for p in example]},
    ]
    graph[1]["hasPart"] = sorted(graph[1]["hasPart"], key=canonical.sort_key)
    entities[DESCRIPTION]["about"] = ref(V.PROFILE)
    rest = sorted(graph[2:] + list(entities.values()) + defined_terms(), key=lambda e: e["@id"])
    return {"@context": V.context(), "@graph": graph[:2] + rest}


# -- the README --------------------------------------------------------------------------------------------------------
def entity_json(e):
    return json.dumps(e, indent=2, sort_keys=True, ensure_ascii=True)


def readme():
    g = groups()
    total = sum(len(s) for s in g.values())
    must = sum(len(s) for p, s in g.items() if level_of(p) == "must")
    should = sum(len(s) for p, s in g.items() if level_of(p) == "should")
    pe = V.profile_entities()
    out = ["<!-- GENERATED by tools/gen_profile.py from qro/vocabulary.py. Edit the definition and run --write. -->", "",
           f"# {V.PROFILE_NAME} {V.PROFILE_VERSION}", "",
           "QRO-Crate is an RO-Crate 1.3 profile for quantum runs, and a checker that holds a crate to it. A crate is "
           "accepted or refused by a name and a location, by `python -m qro check`; this page and the files beside it "
           "describe the profile to a person and to tools that read RO-Crates.", "",
           "## Status", "",
           "- **The IRIs are provisional.** This page is the profile's IRI, and the vocabulary page "
           "([docs/VOCABULARY.md](../docs/VOCABULARY.md)) is its namespace. They are placeholders until a permanent "
           "IRI is registered, which changes every crate's identity: no crate is to be published or archived under a "
           "provisional one.",
           f"- **Version {V.PROFILE_VERSION}**, under CC BY 4.0. Its `datePublished`, {DATE_PUBLISHED}, is the day of the "
           "build and a placeholder: nothing is published yet, and the date is set when the profile is released.", "",
           "## The checker is the authority", "",
           "The shapes below are written for tools that read RO-Crates and cannot run the checker. They never decide a "
           "verdict. Each says in its `claims` which refusals of the checker it mirrors, and every must shape adds the six "
           "refusals of steps 1 and 2 that can come before its own and that RDF cannot show: `spelling`, `term-unknown`, "
           "`graph-form`, `context`, `file-missing` and `file-link`. When a must shape fails, the checker refuses the "
           "crate; and when the crate is one fault away from one the checker accepts, it refuses it by one of the names the "
           "failing shapes claim. Tests hold that over every plant in this directory, a fuzz, every single edit of the "
           "fixture that a pool of 12,591 makes, 469 crates of three families beside it, 124 crates with a key spelt "
           "another way, and a walk over any parcel's accepted crate plants (none is built yet). It is not proved, limit 1 "
           "says over what, limit 19 says what is held of ids and at which base, and what the shapes do not say is the "
           "checker's alone (see the limits below).", "",
           "## Declaring conformance", "",
           "A QRO crate's root data entity `conformsTo` exactly Process Run Crate and this profile:", "",
           f"- `{V.PROCESS_RUN_CRATE}`", f"- `{V.PROFILE}`", "",
           "and the crate holds a contextual entity for each, as RO-Crate 1.3 requires, exactly:", "", "```json",
           ]
    out += [entity_json(e) + "\n" for e in pe]
    out += ["```", "",
            "A crate that declares another version is refused `context`: this reader reads one version of each profile. "
            f"The crate's `@context` is RO-Crate 1.3's, then `{{\"{V.PREFIX}\": \"{V.NAMESPACE}\"}}`, and nothing else. "
            "A term's meaning never changes under its name; a changed meaning is a new term.", "",
            "## Requirement levels", "",
            "| level | folder | severity | what a failure means | shapes |", "|---|---|---|---|---|",
            f"| must | `validator/{TOKEN}/must/` | Violation | the checker refuses the crate; one fault from an accepted crate, by a name a failing shape claims (limit 1) | {must} |",
            f"| should | `validator/{TOKEN}/should/` | Warning | the format states a rule the checker leaves to the producer: "
            f"absence is written as a word (rule 2) | {should} |",
            "| may | none | Info | nothing in the format is an optional behaviour a shape can state, so no folder is "
            "written | 0 |", "",
            "## What the shapes cannot see", ""]
    out += [f"{i}. **{title}** {text}" for i, (title, text) in enumerate(LIMITS, 1)]
    out += ["", "## The vocabulary, the refusals and the controls", "",
            "- [docs/VOCABULARY.md](../docs/VOCABULARY.md): every term and type, its kind, its one spelling and the step "
            "that re-derives it;", "- [docs/REFUSALS.md](../docs/REFUSALS.md): every name a crate is refused by;",
            "- [docs/CONTROLS.md](../docs/CONTROLS.md): every planted fault and what must come of it.", "",
            "## The resources of this Profile Crate", "",
            "| role | file | what it is |", "|---|---|---|",
            f"| specification | [{DESCRIPTION}]({DESCRIPTION}) | this page |",
            f"| vocabulary | [{CONTEXT}]({CONTEXT}) | the context a QRO crate inlines; its entity has the provisional "
            f"absolute IRI {CONTEXT_IRI} (limit 11) |",
            "| vocabulary | [docs/VOCABULARY.md](../docs/VOCABULARY.md) | the vocabulary page, the namespace |",
            f"| validation | [validator/{TOKEN}/](validator/{TOKEN}/) | the shapes as a rocrate-validator profile |",
            f"| example | [{EXAMPLES}]({EXAMPLES}) | the matrix of examples |",
            f"| example | [{FIXTURE_DIR}]({FIXTURE_DIR}) | P0's fixture crate, accepted with `--fixtures` |",
            f"| conformsTo | {V.PROCESS_RUN_CRATE} | the profile this one recommends |", "",
            "## The shapes", "",
            f"{total} shapes: {must} must and {should} should. Each has an anchor; its IRI is this page with the anchor, and "
            "is what `sh:sourceShape` names in a report. `qs:claims` and `qs:kind` are annotations, and are not "
            "constraints.", "",
            '<a id="claims"></a><a id="kind"></a>', ""]
    for path, shapes in g.items():
        out += [f"### validator/{TOKEN}/{path}", "", "| shape | level | what it holds | claims |", "|---|---|---|---|"]
        for s in shapes:
            out.append(f'| <a id="{local_id(s)}"></a>`{local_id(s)}` | {s.level} | {cell(s.name)}: '
                       f'{cell(s.description)} | {cell(", ".join(s.claims) or "none")} |')
        out.append("")
    out += ["## The examples", "",
            f"[{EXAMPLES}]({EXAMPLES}) lists every positive example and every plant and what each layer says of it. "
            f"P0's fixture, in [{FIXTURE_DIR}]({FIXTURE_DIR}), is accepted by `python -m qro check --fixtures`; without "
            "`--fixtures` the checker refuses it `step-unbuilt`, since its raw form and generator are the fixture's.", "",
            "Copyright (c) 2026 Logan W., [CC BY 4.0](" + LICENSE + ").", ""]
    return ascii_md("\n".join(out)).encode("ascii")


def examples_md():
    n_hand, n_gen = len(PLANTS), len(generated())
    out = ["<!-- GENERATED by tools/gen_profile.py from qro/p4_examples.py. Edit the definition and run --write. -->", "",
           "# The examples", "",
           "What the checker and the shapes each say of every example and plant of this profile. It lists what the tests "
           "hold, never what a run printed. Only this profile's own plants are here; every other parcel's crate plants "
           "are held to the shapes' soundness and not listed (a page every parcel's plants regenerate is a merge "
           "conflict).", "",
           "Where the checker says `accepted but for step 9`, steps 1 to 8 held and only step 9 refused, since the "
           "fixture's generator did not make the edited metadata: so every must shape has to conform. The `abstains` "
           "family is the exception, and says so: the reader refuses those crates' ids (FORMAT.md item 22), so the checker "
           "has refused them and the evaluator abstains; a real engine reads them its own way, and the matrix says what it "
           "fails, on crates refused first, by a name the failing shape claims (limit 19: every must shape claims "
           "`spelling` and `graph-form`).", "",
           "## Positive examples", "",
           "| example | the checker says | the shapes say |", "|---|---|---|",
           f"| `{FIXTURE_DIR}`, P0's fixture | accepted with `--fixtures`; `step-unbuilt` without | conforms to every must "
           "shape |",
           "| every term, on an entity its domain admits | the strict reader accepts it; the later steps of the parcels' "
           "terms need files it does not have | conforms to every must shape and every should shape |", "",
           f"## Plants ({n_hand} written, {n_gen} made from the table)", ""]
    for family in FAMILIES:
        rows = [r for r in matrix_rows() if r[0] == family]
        if not rows:
            continue
        out += [f"### {family}", "", "| plant | what was planted | the checker says | the must shapes that fail | why |",
                "|---|---|---|---|---|"]
        out += [f"| `{r[1]}` | {cell(r[2])} | {cell(r[3])} | {cell(r[4])} | {cell(r[5])} |" for r in rows]
        out.append("")
    out += ["### made from the table", "",
            "For each term of the vocabulary, one plant gives it a value in none of its spelling, on an entity its "
            "domain admits (`spell-` and the term): the checker refuses `spelling`, and the term's shape fails. For each "
            "term whose domain is not `*`, one puts it, in its spelling, on an entity of a type its domain does not "
            "admit (`domain-` and the term): the checker refuses `graph-form`, and the domain shape fails. A term "
            "whose bad value is held first by another rule of the reader says so in the tests.", ""]
    return ascii_md("\n".join(out)).encode("ascii")


# -- everything ------------------------------------------------------------------------------------------------------
def read_context(root=None):
    """P0's profile/context.jsonld, as bytes. ContextMissing, with a sentence that says what is there instead, where it is not a
    file this can read: a link is never read through (FORMAT.md item 12), and a directory is no file."""
    path = Path(root or REPO) / "profile" / CONTEXT
    if checker._is_link(path):
        raise ContextMissing(f"profile/{CONTEXT} is a link, not the file tools/gen_vocabulary.py --write writes, and a link is "
                             "never read through: remove it, then run that")
    if path.is_dir():
        raise ContextMissing(f"profile/{CONTEXT} is a directory, not the file tools/gen_vocabulary.py --write writes: remove it, "
                             "then run that")
    try:
        return path.read_bytes()
    except (FileNotFoundError, NotADirectoryError):
        raise ContextMissing(f"profile/{CONTEXT} is missing: run tools/gen_vocabulary.py --write") from None
    except OSError as x:
        raise ContextMissing(f"profile/{CONTEXT} cannot be read ({type(x).__name__}): tools/gen_vocabulary.py --write writes it") from None


def render(root=None):
    """Every generated file of profile/, by path relative to it. P0's context.jsonld is read, listed and digested,
    and not returned. ContextMissing where it is not a file to read."""
    context = read_context(root)
    files = {DESCRIPTION: readme(), EXAMPLES: examples_md(), VALIDATOR + "profile.ttl": profile_ttl()}
    files.update(shapes_files())
    files.update(fixture_files())
    files[canonical.DESCRIPTOR] = canonical.dumps(metadata(files, context))
    return files


def problems():
    """What stops the table being rendered at all: the shapes' own, and every file ASCII. For the generator's exit 2."""
    return shape_problems()


# -- the Profile Crate held to the rules of RO-Crate 1.3's profiles page that its bytes show --------------------------
NET = "the check itself failed on this input"          # a bug of the check: the fuzz of the tests holds that it never shows


def types_of(e):
    """The @type strings of an entity: one string or a list of strings. Anything else names no type, and the rules that
    need a type then refuse the entity."""
    t = e.get("@type") if isinstance(e, dict) else None
    return [x for x in (t if isinstance(t, list) else [t]) if isinstance(x, str)]


def named(v):
    """Whether `v` is a string with something in it."""
    return isinstance(v, str) and v != ""


def check_profile_crate(files, context_bytes=None):
    """The rules of RO-Crate 1.3's profiles page that the bytes of a Profile Crate show, and a few of the core's, for
    `files` ({path: bytes}, the metadata among them): a list of problems in a few words each, empty if it holds. It
    reads any Profile Crate, however misshapen (`files` a mapping; the metadata and the other files may hold anything),
    and raises on none. What it cannot read it refuses, with a problem that names it, and the net below catches only a
    bug of its own, which tests/p4/test_p4_profile_crate.py's fuzz holds never to show.

    Held (MUST): the root is typed Dataset and Profile and declares the human-readable description as a File about it
    that its hasPart lists; a profile the root is a profile of has a contextual Profile entity; an entity that conforms
    to JSON-LD's Context has an absolute @id and the encodingFormat application/ld+json. Held (SHOULD): the root's
    absolute @id, name, isProfileOf and hasPart; for each resource descriptor a role among W3C's eight (or
    dct:conformsTo), an artifact, and on each artifact an encodingFormat. Held from the core: the root's name,
    description, license, datePublished and version; every File's digest, size and encodingFormat, and a File for every
    file; every reference resolves; every File and Dataset is reached from the root through hasPart; the vocabulary's
    DefinedTerms are the table's. NOT held, and stated as limits (profile/README.md, 9, 11, 17 and 22): the description is
    Markdown where RO-Crate asks HTML; the context's IRI is not a permalink and is not versioned; the extension terms
    are mapped by one prefix, not each by its code; nothing was checked by RO-Crate's own validator. P4's own check, not
    the QRO checker: a Profile Crate is no QRO crate."""
    try:
        return _check(files, context_bytes)
    except Exception as x:
        return [f"{NET}: {type(x).__name__}"]


def _check(files, context_bytes):
    out = []
    data = dict(files)
    if context_bytes is not None:
        data[CONTEXT] = context_bytes
    try:
        md = json.loads(data[canonical.DESCRIPTOR])
    except (KeyError, TypeError, ValueError, RecursionError) as x:
        return [f"the Profile Crate's metadata is not readable: {type(x).__name__}"]
    if not isinstance(md, dict) or md.get("@context") != V.context() or not isinstance(md.get("@graph"), list):
        return ["the metadata is an @context of RO-Crate 1.3's and the qro prefix, and an @graph"]
    graph = {}
    for e in md["@graph"]:
        i = e.get("@id") if isinstance(e, dict) else None
        if not named(i):
            out.append("an entity is an object with an @id that is a string")
        elif i in graph:
            out.append(f"{i}: an entity twice")
        else:
            graph[i] = e
    kind = {i: frozenset(types_of(e)) for i, e in graph.items()}          # each entity's types, read once

    def refs(e, key):
        """The ids under `key` of the entity `e`: each value a reference {"@id": string}, alone or in a list. A value
        that is none is a problem here, and is left out."""
        if key not in e:
            return []
        v = e[key]
        got = []
        for x in (v if isinstance(v, list) else [v]):
            if isinstance(x, dict) and list(x) == ["@id"] and isinstance(x["@id"], str):
                got.append(x["@id"])
            else:
                out.append(f"{e['@id']}: {key} holds a value that is no reference of the form {{\"@id\": ...}}")
        return got

    d = graph.get(canonical.DESCRIPTOR)
    if d is None or "CreativeWork" not in kind[canonical.DESCRIPTOR] or refs(d, "conformsTo") != [V.ROCRATE]:
        out.append("the descriptor is a CreativeWork that conformsTo RO-Crate 1.3")
    about = refs(d, "about") if d else []
    root = graph.get(about[0]) if len(about) == 1 else None
    if root is None:
        return list(dict.fromkeys(out + ["the descriptor is about one entity, the root, which the graph holds"]))
    rid = root["@id"]
    if not {"Dataset", "Profile"} <= kind[rid]:
        out.append("the root is typed Dataset and Profile")
    if S.IRI.fullmatch(rid) is None:
        out.append("the root's @id is an absolute IRI")
    for key in ("name", "description", "license", "datePublished", "version", "isProfileOf", "hasPart"):
        if key not in root:
            out.append(f"the root has no {key}")
    if "datePublished" in root and S.problem("date", root["datePublished"]):
        out.append("the root's datePublished is an ISO date")
    if root.get("version") != V.PROFILE_VERSION:
        out.append("the root's version is the profile's")
    if refs(root, "isProfileOf") != [V.ROCRATE]:
        out.append("the root is a profile of RO-Crate 1.3")
    for i in refs(root, "hasPart") + refs(root, "hasResource") + refs(root, "isProfileOf") + refs(root, "license"):
        if i not in graph:
            out.append(f"the root names {i}, which the graph does not hold")
    spec = [i for i in refs(root, "hasPart") if i in graph and "File" in kind[i]
            and refs(graph[i], "about") == [rid]]
    if not spec:
        out.append("the root's hasPart holds the human-readable description, a File about the root")
    elif not any(named(graph[i].get("encodingFormat")) for i in spec):
        out.append("the description names its encodingFormat")
    for r in refs(root, "hasResource"):
        e = graph.get(r)
        if e is None or "ResourceDescriptor" not in kind[r]:
            out.append(f"{r}: a hasResource names a ResourceDescriptor")
            continue
        roles = refs(e, "hasRole")
        if len(roles) != 1 or not (roles[0] in [ROLE + x for x in ROLES] or roles[0] == DCT_CONFORMS):
            out.append(f"{r}: a role among W3C's eight, or dct:conformsTo")
        artifacts = refs(e, "hasArtifact")
        if not artifacts:
            out.append(f"{r}: a ResourceDescriptor names an artifact")
        for a in artifacts:
            if a not in graph and not (roles == [DCT_CONFORMS] and S.IRI.fullmatch(a)):
                out.append(f"{r}: the artifact {a} is no entity of the crate")
            if roles == [DCT_CONFORMS] and "Profile" not in kind.get(a, ()):
                out.append(f"{r}: a recommended profile has its contextual Profile entity")
            if a in graph and not named(graph[a].get("encodingFormat")):
                out.append(f"{r}: the artifact {a} declares its encodingFormat")
    for i, e in graph.items():
        if "File" in kind[i]:
            if i not in data:
                out.append(f"{i}: a File whose file is not there")
                continue
            body = data[i]
            if not isinstance(body, (bytes, bytearray)):
                out.append(f"{i}: a file that is no bytes")
            elif e.get("sha256") != sha(body) or e.get("contentSize") != str(len(body)):
                out.append(f"{i}: the digest or the size is not the file's")
            if not named(e.get("encodingFormat")):
                out.append(f"{i}: a File names its encodingFormat")
        for part in refs(e, "hasPart"):
            if part not in graph:
                out.append(f"{i}: lists {part}, which the graph does not hold")
    listed = {i for i, k in kind.items() if "File" in k}
    for p in sorted(k for k in data if isinstance(k, str)):
        if p != canonical.DESCRIPTOR and p not in listed:
            out.append(f"{p}: a file no entity lists")
    reached, stack = set(), [rid]
    while stack:                                   # the data entities the root links, directly or through a Dataset
        for part in refs(graph.get(stack.pop(), {}), "hasPart"):
            if part not in reached:
                reached.add(part)
                stack.append(part)
    for i in sorted(k for k in graph if k != rid and k not in reached):
        if {"File", "Dataset"} & kind[i]:
            out.append(f"{i}: a data entity the root does not reach through hasPart")
    profiles = {i for i, k in kind.items() if "Profile" in k and "Dataset" not in k}
    for i in refs(root, "isProfileOf"):
        if i not in profiles:
            out.append(f"{i}: a profile named has a contextual Profile entity")
    terms = {i for i, e in graph.items() if "DefinedTerm" in kind[i] and refs(e, "inDefinedTermSet") == [V.NAMESPACE]}
    if terms != defined_term_ids():
        out.append("the DefinedTerms are the table's qro: terms and types, no more and no fewer")
    contexts = [i for i, e in graph.items() if JSONLD_CONTEXT in refs(e, "conformsTo")]
    if not contexts:
        out.append("the profile's JSON-LD context has its entity, which conforms to JSON-LD's Context")
    for i in contexts:
        if S.IRI.fullmatch(i) is None:
            out.append(f"{i}: an entity that represents a JSON-LD context has an absolute @id")
        if graph[i].get("encodingFormat") != JSONLD_FORMAT:
            out.append(f"{i}: an entity that represents a JSON-LD context has the encodingFormat application/ld+json")
    return list(dict.fromkeys(out))
