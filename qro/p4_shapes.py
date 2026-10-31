"""The shapes, generated from qro/vocabulary.py's table (P4's design, item 4.4): a row and its shape cannot disagree,
because the shape is the row rendered.

  - a term shape a row (`term-*`): the row's one spelling, its absence words, and one value if it is single-valued;
  - a domain shape a row whose domain is not `*` (`domain-*`): the term stands only where its domain admits it;
  - the structural shapes, from the table's own functions and lists (V.descriptor(), V.ROOT_REQUIRED,
    V.profile_entities()) and from PRESENCE below;
  - a should-level shape for each term with absence words on a typed domain (`absence-*`): rule 2.

A shape never claims more than the checker holds (P4's design, item 4.6). Each is written to be at most as strict as
the checker for the crates a SHACL engine can see, and says which refusals it mirrors, in `claims`. Two things are held,
and the second is narrower than the first:
  - when a must shape fails, the checker refuses the crate (steps 1 to 3): over every plant, every crate a fuzz makes,
    and every single edit of the fixture a sweep makes (tests/p4/test_p4_examples.py, test_p4_sweeps.py);
  - when the crate is one fault away from one the checker accepts, it refuses it by a name that one of the failing
    shapes claims: over the plants, the pool of edits, the three families of additions and the alias-key crates the
    sweeps make (not proved). A crate with several faults is refused too, but its first refusal can be a fault that no
    failing shape mirrors, and then the name is not claimed: that is not held, and not said.
A shape is built with the refusals it mirrors, its own; `groups` and `build` add FORM below to every must shape's
claims: the six refusals of steps 1 and 2 that can come before a shape's own and that RDF cannot show (`widen=False`
leaves them out, and the gates read the plants against the own ones). The gates are tests/p4/test_p4_examples.py
(soundness over every plant, and over every plant of any parcel whose control row says `accepted`: none is built yet),
test_p4_sweeps.py (the sweeps), test_p4_spelling.py (every spelling against qro/spelling.py's own verdict) and
test_p4_gates.py (each gate watched failing). What a shape cannot see is the checker's alone, and docs/P4.md lists it,
limit by limit.

Where a shape is looser than the checker, it is looser on purpose and the description says so: the real time or date,
lowest terms, an exact decimal, a control character, and `2^63 - 1` for a size are not a pattern's to hold. Every
pattern is in the syntax Python's `re` and an XPath engine share (no `(?`, `\\d`, `\\w`, `\\p`, `\\x`, back-reference or
lazy quantifier), and every regular expression that qro/spelling.py has is read from there, never written again.
Stdlib only.
"""
import re
from dataclasses import replace

from qro import spelling as S
from qro import vocabulary as V
from qro.p4_expand import iri_of_term
from qro.p4_model import RDF_TYPE, XSD_INTEGER, XSD_STRING, Lit, Shape, inv, one_or_more, walk
from qro.p4_model import problems as shape_problems

PREFIX_SHAPES = "qs"
FILES = ("must/1_structure.ttl", "must/2_terms.ttl", "must/3_domains.ttl", "should/1_absence.ttl")
# Presence: what an entity of a kind must carry that the table, which says only where a term may stand, does not say.
# P4's own until the table has a `need` for it (P4's design, R-A, declined for now); the root's is V.ROOT_REQUIRED.
# Held two ways against the checker by tests/p4/test_p4_examples.py: removing a term from an entity of its kind is
# refused where this says it is required, and accepted where it says nothing.
PRESENCE = {"File": ("sha256", "contentSize"), "qro:RawResult": ("qro:rawForm",)}
TEXT_PATTERN = r"^[^\s]([\s\S]*[^\s])?$"      # not empty, no white space at an end: `\s` is Python's, wider than XPath's
KIND_PHRASE = {
    "CHECKED": "the form only: step {step} re-derives the value",
    "READ": "the form only: the checker's arithmetic takes the value as given",
    "ANCHORED": "stated, not checked, until the crate holds the provider's own record of it",
    "REPORTED": "stated, not checked",
}
# What a pattern may not use, for the engines that read it other than Python's (the portable subset).
NON_PORTABLE = ((r"\(\?", "a (? group"), (r"\\[dDwWbBAZ]", r"\d, \w, \b, \A or \Z"), (r"\\[pP]\{", r"\p{}"),
                (r"\\x[0-9a-fA-F]", r"\x"), (r"\\[0-9]", "a back-reference"), (r"[*+?}][?+]", "a lazy or possessive quantifier"))


# The refusals of steps 1 and 2 that can come before a shape's own, and that RDF cannot show, or shows as another graph. So any
# must shape can fail on a crate the checker refuses by one of them, and every must shape claims all six, in this order:
#   spelling      an empty list, a list of one, a bare value where a list stands: another graph in RDF;
#   term-unknown  a key or a type spelt another way (`schema:name` for `name`, `MediaObject` for `File`): the same predicate or
#                 class in RDF (P4's verifier, round 1, defect 2: 202 of 12,591 single edits of the fixture, and 65 of 124
#                 crates with an alias key, had a shape fail under a name it did not claim);
#   graph-form    an @id twice (RDF merges the nodes, so a single-valued term has two values); two paths that differ only by
#                 case, or a path that is a file and a directory (RDF holds two nodes, and the one added, a File with no digest,
#                 fails a shape); a reference that names no entity (`_:b0` is a blank node to a real engine); a top-level
#                 @reverse, which a JSON-LD reader reads as a triple (P4's verifier, round 2, defect 1);
#   context       a top-level @context other than the reader's: a real engine reads the crate's own, so a term it redefines is
#                 another predicate, and the evaluator abstains (round 2, defect 1);
#   file-missing  a File entity with no file under its name (an added entity has none on disk): step 2 refuses it before the
#                 digest and the listing, whichever shape the entity fails (round 2, defect 1);
#   file-link     a link in the crate: step 2's walk refuses it before anything else of step 2 (the lead's ruling of
#                 2026-10-26T11:18:27Z, from reading checker.walk; a test plants it where the host can make a link).
# The reader refuses `field-kind` at a key that RO-Crate's context defines, which the closed `entity` shape claims; the later
# refusals of step 2 (`file-unlisted`, `file-digest`, `raw-digest`) are claimed by the shapes that mirror them. Step 3 is the same:
# `raw-form` is `rawresult-form`'s, and `count-unpaid` is no shape's, since no one-edit crate that reaches it fails a must shape
# (a stated count the bytes do not hold is a number to RDF); tests/p4/test_p4_sweeps.py pins both.
FORM = ("spelling", "term-unknown", "graph-form", "context", "file-missing", "file-link")


def claims_of(*own):
    """A must shape's claims: the refusals it mirrors, then FORM's six where it does not name them already."""
    return tuple(own) + tuple(f for f in FORM if f not in own)


def widened(shape):
    """A must shape with FORM added to its claims. A should shape is left as it is: the checker accepts what it asks."""
    return replace(shape, claims=claims_of(*shape.claims)) if shape.level == "must" else shape


class TableProblem(ValueError):
    """The table, as it stands, cannot be rendered as shapes: the generator answers it as the definitions
    contradicting themselves (exit 2)."""


def slug(key):
    """A key as a lowercase kebab: the shape ids' local names and the README's anchors, which GitHub lowercases."""
    return key.replace(":", "-").lower()


def shape_iri(local):
    return V.PROFILE + "#" + local


def term_iri(key):
    """The IRI of a term or a type: this profile's namespace for a qro: name, else RO-Crate's context."""
    if key.startswith(V.PREFIX + ":"):
        return V.NAMESPACE + key[len(V.PREFIX) + 1:]
    try:
        return iri_of_term(key)
    except KeyError:
        raise TableProblem(f"{key}: neither a {V.PREFIX}: name nor a term of RO-Crate 1.3's context") from None


def prefixes():
    """The prefixes of every file the generator writes, in a fixed order."""
    return (("sh", "http://www.w3.org/ns/shacl#"), ("rdf", "http://www.w3.org/1999/02/22-rdf-syntax-ns#"),
            ("xsd", "http://www.w3.org/2001/XMLSchema#"), ("schema", "http://schema.org/"),
            ("dct", "http://purl.org/dc/terms/"), ("prof", "http://www.w3.org/ns/dx/prof/"),
            (PREFIX_SHAPES, V.PROFILE + "#"), (V.PREFIX, V.NAMESPACE))


# -- one function a spelling: the value constraints --------------------------------------------------------------
def whole(pattern):
    """A regular expression of qro/spelling.py's, made to match the whole string. A group, never (?:...)."""
    return f"^({pattern})$"


def _text():
    return dict(datatype=XSD_STRING, min_length=1, pattern=TEXT_PATTERN)


SPELLING_SHAPES = {
    "integer": lambda: dict(datatype=XSD_INTEGER, min_inclusive=0, max_inclusive=S.MAX),
    "size": lambda: dict(datatype=XSD_STRING, pattern=whole(S.PATTERNS["size"].pattern), max_length=len(str(S.MAX))),
    "digest": lambda: dict(datatype=XSD_STRING, pattern=whole(S.PATTERNS["digest"].pattern), max_length=64),
    "commit": lambda: dict(datatype=XSD_STRING, pattern=whole(S.PATTERNS["commit"].pattern), max_length=40),
    "rational": lambda: dict(datatype=XSD_STRING, pattern=whole(S.PATTERNS["rational"].pattern),
                             max_length=2 * S.TERM_DIGITS + 2),
    "binary64": lambda: dict(datatype=XSD_STRING, pattern=whole(S.PATTERNS["binary64"].pattern)),
    "time": lambda: dict(datatype=XSD_STRING, pattern=whole(S.PATTERNS["time"].pattern)),
    "date": lambda: dict(datatype=XSD_STRING, pattern=whole(S.PATTERNS["date"].pattern), max_length=10),
    "text": _text,
    "iri": lambda: dict(datatype=XSD_STRING, pattern=whole(S.PATTERNS["iri"].pattern)),
    "ref": lambda: dict(node_kind="IRI"),
    "slot": lambda: None,
}


def spelling_constraints(spelling):
    """The value constraints of one spelling as Shape keywords, or None for a slot, whose only value is an absence
    word. TableProblem for a spelling this module has no constraint for."""
    base, _, rest = spelling.partition(":")
    if base == "word":
        if rest not in V.WORDS:
            raise TableProblem(f"{spelling}: names no word set")
        return dict(datatype=XSD_STRING, in_=tuple(Lit(w) for w in V.WORDS[rest]))
    if spelling not in SPELLING_SHAPES:
        raise TableProblem(f"{spelling}: a spelling with no shape constraint")
    return SPELLING_SHAPES[spelling]()


def spelling_words(t):
    """What the shape says a term's value is, from the table: for the description."""
    base, _, rest = t.spelling.partition(":")
    if base == "word":
        return f"one of the {rest} words: " + ", ".join(V.WORDS[rest])
    return V.SPELLINGS[base]


def kind_phrase(t):
    return KIND_PHRASE[t.kind].format(step=t.step)


def domain_text(t):
    return ", ".join(t.domain)


# -- the shapes a row makes ----------------------------------------------------------------------------------------
def term_shape(t):
    """The row's one spelling: the term's value is in it or is an absence word the row allows, and a single-valued
    term has one value."""
    p = term_iri(t.key)
    base = spelling_constraints(t.spelling)
    absent = tuple(Lit(a) for a in t.absent)
    if base is None and not absent:
        raise TableProblem(f"{t.key}: a slot with no absence word")
    value = dict(in_=absent) if base is None else dict(or_=(Shape(**base), Shape(in_=absent))) if absent else base
    message = f"{t.key} is not in its one spelling ({t.spelling}" + (f", or {', '.join(t.absent)}" if t.absent else "") + ")"
    prop = Shape(path=p, max_count=None if t.many else 1, message=message, **value)
    description = (spelling_words(t) + (f"; or, in place of a value, {', '.join(t.absent)}" if t.absent else "")
                   + "; " + ("a list of one value or more" if t.many else "one value") + "; " + kind_phrase(t))
    return Shape(id=shape_iri("term-" + slug(t.key)), targets=(("subjectsOf", p),), props=(prop,), claims=("spelling",),
                 kind=t.kind, name=f"{t.key}: its one spelling", description=description, message=message)


def domain_alternative(token):
    """The node shape of one domain token: where the table lets a term stand."""
    if token == V.ROOT:
        return Shape(props=(Shape(path=inv(term_iri("about")), min_count=1),))          # the object of the descriptor's about
    if token == V.DESC:
        return Shape(pattern=r"(^|/)" + V.DESC.replace(".", r"\.") + "$")
    if token == V.LOCAL:
        return Shape(classes=(term_iri("File"),))                                         # looser: any File (limit 4)
    return Shape(classes=(term_iri(token),))


def domain_shape(t):
    """The term stands only on the entities its domain admits. None for a term that stands anywhere."""
    if "*" in t.domain:
        return None
    alternatives = [domain_alternative(tok) for tok in t.domain]
    shape = Shape(or_=tuple(alternatives)) if len(alternatives) > 1 else alternatives[0]
    message = f"{t.key} stands only on {domain_text(t)}"
    notes = [text for token, text in ((V.LOCAL, "a File here is any File"), (V.ROOT, "the root is what the descriptor is "
                                      "about"), (V.DESC, "the descriptor is the entity named " + V.DESC))
             if token in t.domain]
    return replace(shape, id=shape_iri("domain-" + slug(t.key)), targets=(("subjectsOf", term_iri(t.key)),),
                   claims=("graph-form",), name=f"{t.key}: where it may stand", message=message,
                   description=f"stands only on {domain_text(t)}" + (": " + "; ".join(notes) if notes else ""))


def absence_shapes():
    """Rule 2: absence is written as a word. A term with absence words, on a typed domain, SHOULD be on each entity
    of that type: the value, or one of its words. The checker accepts an entity without it (it is a Warning)."""
    out = []
    for t in V.TERMS:
        types = [tok for tok in t.domain if tok not in ("*", V.ROOT, V.DESC, V.LOCAL)]
        if not t.absent or not types or len(types) != len(t.domain):
            continue
        for tok in types:
            message = f"{tok} should carry {t.key}, or say {' or '.join(t.absent)}"
            out.append(Shape(id=shape_iri("absence-" + slug(t.key) + "-" + slug(tok)), level="should",
                             targets=(("class", term_iri(tok)),), name=f"{tok}: {t.key} or an absence word",
                             description="rule 2: absence is a word, never a term left out; the checker accepts "
                                         "an entity without it", message=message,
                             props=(Shape(path=term_iri(t.key), min_count=1, message=message),)))
    return out


# -- the structural shapes: rules the reader and the checker hold as code, read here from the table's own functions --
def needs(kind):
    return tuple(term_iri(k) for k in PRESENCE[kind])


def action_classes():
    return tuple(term_iri(y.key) for y in V.TYPES if y.action)


def any_of(classes):
    """The value is an instance of one of the classes: sh:class for one, else sh:or of them."""
    return dict(classes=classes) if len(classes) == 1 else dict(or_=tuple(Shape(classes=(c,)) for c in classes))


def entity_shape():
    term_iris = list(dict.fromkeys(term_iri(t.key) for t in V.TERMS))
    return Shape(
        id=shape_iri("entity"), claims=("term-unknown", "field-kind", "graph-form"),
        name="every entity: a named node of listed types, carrying only the profile's terms",
        description="an entity is an IRI, has a type from the table, and carries no key the table does not name; "
                    "a key neither the table nor RO-Crate's context names never reaches RDF, so it is the "
                    "checker's alone",
        message="an entity is a named node, of listed types, with only the profile's terms",
        targets=(("subjectsOf", RDF_TYPE),) + tuple(("subjectsOf", p) for p in term_iris),
        node_kind="IRI", closed=True, ignored=(RDF_TYPE,) + tuple(term_iris),
        props=(Shape(path=RDF_TYPE, min_count=1, in_=tuple(term_iri(y.key) for y in V.TYPES),
                     message="an entity has a type, and it is one the profile lists"),))


def descriptor_shape():
    """The metadata descriptor as V.descriptor() states it: its type, what it is about, what it conforms to, nothing
    more. The root is the node it is about, whose IRI ends in a slash on any base, so that is what is held."""
    d = V.descriptor()
    if d["about"] != {"@id": V.ROOT}:
        raise TableProblem("the descriptor is about the root, ./")
    types = d["@type"] if isinstance(d["@type"], list) else [d["@type"]]
    conforms = [x["@id"] for x in d["conformsTo"]]
    about, conformsto = term_iri("about"), term_iri("conformsTo")
    return Shape(
        id=shape_iri("descriptor"), claims=("graph-form",), name="the metadata descriptor",
        description="a CreativeWork about the root that conformsTo RO-Crate 1.3, and nothing more",
        message="the descriptor is a CreativeWork about the root that conformsTo RO-Crate 1.3, and nothing more",
        targets=(("subjectsOf", about),), pattern=r"(^|/)" + V.DESC.replace(".", r"\.") + "$",
        closed=True, ignored=(RDF_TYPE,),
        props=(Shape(path=RDF_TYPE, min_count=len(types), max_count=len(types),
                     has_value=tuple(term_iri(t) for t in types)),
               Shape(path=about, min_count=1, max_count=1, node_kind="IRI", pattern="/$"),
               Shape(path=conformsto, min_count=len(conforms), max_count=len(conforms), has_value=tuple(conforms))))


def root_shape():
    """The root: a Dataset, never an action, carrying each term the profile requires of it, conformsTo exactly
    Process Run Crate and this profile, mentioning only actions. What its hasPart names is the checker's: it holds
    that a listed file is there and every file is listed, and nothing of what kind of entity is listed."""
    mentions = term_iri("mentions")
    required = tuple(Shape(path=term_iri(k), min_count=1) for k in V.ROOT_REQUIRED if k != "conformsTo")
    conforms = (V.PROCESS_RUN_CRATE, V.PROFILE)
    return Shape(
        id=shape_iri("root"), claims=("graph-form",), name="the root data entity",
        description="a Dataset, never an action, with every term the profile requires of a root, conformsTo exactly "
                    "Process Run Crate and this profile, mentioning only actions",
        message="the root is a Dataset, never an action, with the terms the profile requires of it",
        targets=(("objectsOf", term_iri("about")),), classes=(term_iri("Dataset"),),
        not_=(Shape(**any_of(action_classes())),),
        props=required + (Shape(path=term_iri("conformsTo"), min_count=len(conforms), max_count=len(conforms),
                                has_value=conforms),
                          Shape(path=mentions, **any_of(action_classes()))))


def action_mentioned_shape():
    return Shape(id=shape_iri("action-mentioned"), claims=("graph-form",), name="every action is mentioned by the root",
                 description="the root mentions every action in the crate",
                 message="an action the root does not mention",
                 targets=tuple(("class", c) for c in action_classes()),
                 props=(Shape(path=inv(term_iri("mentions")), min_count=1, message="an action the root does not mention"),))


def file_digest_shape():
    """A File the crate holds names its digest and size. A File whose IRI is not a file: IRI, or holds a #, is not
    a path in the crate (the expansion reads a relative id against a file: base, and refuses an absolute file: one),
    so the checker asks nothing of it (limit 4)."""
    return Shape(
        id=shape_iri("file-digest-present"), claims=("file-digest", "raw-digest"),
        name="a File the crate holds names its digest and size",
        description="a File with a path in the crate carries sha256 and contentSize; one whose IRI is not a file: "
                    "IRI, or holds a #, is not held to it",
        message="a File the crate holds names its digest and size", targets=(("class", term_iri("File")),),
        or_=(Shape(pattern="#"), Shape(not_=(Shape(pattern="^file:"),)),
             Shape(props=tuple(Shape(path=p, min_count=1) for p in needs("File")))))


def file_reached_shape():
    root = Shape(props=(Shape(path=inv(term_iri("about")), min_count=1),))
    return Shape(
        id=shape_iri("file-reached"), claims=("file-unlisted", "graph-form"),     # graph-form: a reference that names nothing
        name="a File with a digest is reached from the root",
        description="every File with a sha256 is reached from the root through hasPart; a file on disk that no "
                    "entity lists is the checker's alone",
        message="a File that no hasPart reaches from the root", targets=(("subjectsOf", term_iri("sha256")),),
        props=(Shape(path=one_or_more(inv(term_iri("hasPart"))), qvs=((root, 1),),
                     message="a File that no hasPart reaches from the root"),))


def raw_result_shape():
    return Shape(
        id=shape_iri("rawresult-form"), claims=("raw-form", "graph-form", "file-unlisted"),
        name="a raw result is a File and names its raw form",
        description="a raw result is a File and names the form its bytes take; its shots are counted from its bytes "
                    "by the checker, never stated beside them",
        message="a raw result is a File and names its raw form", targets=(("class", term_iri("qro:RawResult")),),
        classes=(term_iri("File"),), props=tuple(Shape(path=p, min_count=1) for p in needs("qro:RawResult")))


def profile_shapes():
    """Each profile the root conformsTo has its contextual entity, exactly as V.profile_entities() states it, and no
    Profile entity besides. The version is held by its own shape, since the checker refuses it by another name."""
    entities = V.profile_entities()
    iris = tuple(e["@id"] for e in entities)
    targets = tuple(("node", i) for i in iris)
    name, version = term_iri("name"), term_iri("version")
    whole_entity, versions = [], []
    for e in entities:
        types = e["@type"] if isinstance(e["@type"], list) else [e["@type"]]
        whole_entity.append(Shape(
            has_value=(e["@id"],), closed=True, ignored=(RDF_TYPE,),
            props=(Shape(path=RDF_TYPE, min_count=len(types), max_count=len(types),
                         has_value=tuple(term_iri(t) for t in types)),
                   Shape(path=name, min_count=1, max_count=1, has_value=(Lit(e["name"]),)),
                   Shape(path=version))))
        versions.append(Shape(has_value=(e["@id"],),
                              props=(Shape(path=version, min_count=1, max_count=1, has_value=(Lit(e["version"]),)),)))
    return [
        Shape(id=shape_iri("profile-entities"), claims=("graph-form",),
              name="each profile the root conformsTo has its contextual entity",
              description="the contextual entity of this profile and of Process Run Crate, each with its type and "
                          "name as the table states them, and no other Profile entity",
              message="a profile's contextual entity is missing, or is not as the table states it",
              targets=targets + (("class", term_iri("Profile")),), or_=tuple(whole_entity)),
        Shape(id=shape_iri("profile-version"), claims=("context", "graph-form"),
              name="each profile's contextual entity declares the version the table holds",
              description="this reader reads one version of each profile: another is refused as context",
              message="a profile's contextual entity declares another version than this reader reads",
              targets=targets, or_=tuple(versions))]


def structural():
    return [entity_shape(), descriptor_shape(), root_shape(), action_mentioned_shape(), file_digest_shape(),
            file_reached_shape(), raw_result_shape()] + profile_shapes()


def groups(widen=True):
    """{file path under validator/qro-crate/: its shapes}, in a fixed order. A file with no shape is not written
    ("may" is empty: nothing in the format is optional behaviour a shape can state). Every must shape's claims have
    FORM's six added, unless `widen` is False, which gives the refusals each shape mirrors, its own."""
    out = {"must/1_structure.ttl": structural(), "must/2_terms.ttl": [term_shape(t) for t in V.TERMS],
           "must/3_domains.ttl": [s for s in (domain_shape(t) for t in V.TERMS) if s is not None],
           "should/1_absence.ttl": absence_shapes()}
    return {path: [widened(s) if widen else s for s in shapes] for path, shapes in out.items() if shapes}


def build(widen=True):
    """Every shape, in file order."""
    return [s for shapes in groups(widen).values() for s in shapes]


def level_of(path):
    return path.split("/", 1)[0]


def problems():
    """What stops the table being rendered as shapes, in a few words each: the generator's exit 2. The table's own
    contradictions are V.sanity()'s, which the generator reads and this does not write again."""
    out = []
    for sp in V.SPELLINGS:
        if sp not in SPELLING_SHAPES:
            out.append(f"spelling {sp}: no shape constraint")
    for sp in SPELLING_SHAPES:
        if sp not in V.SPELLINGS:
            out.append(f"spelling {sp}: has a shape constraint and is no spelling of the table")
    try:
        shapes = build()
    except TableProblem as x:
        return out + [str(x)]
    ids = [s.id for s in shapes]
    for i in sorted({i for i in ids if ids.count(i) > 1}):
        out.append(f"two shapes share the id {i}")
    for path, group in groups().items():
        for s in group:
            out += shape_problems(s)
            if s.level != level_of(path):
                out.append(f"{s.id}: level {s.level} in a {level_of(path)} folder")
            for c in s.claims:
                if c not in V.REFUSAL:
                    out.append(f"{s.id}: claims {c}, which is no refusal")
    for s in shapes:
        for shape in walk(s):
            if shape.pattern is not None:
                for rx, why in NON_PORTABLE:
                    if re.search(rx, shape.pattern):
                        out.append(f"{s.id}: pattern {shape.pattern!r} uses {why}, outside the syntax an engine shares")
    return out
