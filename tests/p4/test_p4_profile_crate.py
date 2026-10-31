"""The Profile Crate and the files that go with it (qro/p4_profile.py): what the generator makes, and what
`check_profile_crate` holds it to, each rule of RO-Crate 1.3's Profile Crate (READ 2026-10-16, the profiles page of the
specification) planted. The README's anchors are the shapes' ids, both ways; the matrix lists the plants it should; every file is
ASCII with LF line ends. The directory on disk is what the generator renders."""
import copy
import hashlib
import json
import re
from pathlib import Path

import pytest
from p4_helpers import ROOT, prepare, turtle_problems
from qro import canonical, fixture
from qro import p4_examples as X
from qro import p4_profile as P
from qro import p4_shapes as H
from qro import vocabulary as V

PROFILE = ROOT / "profile"


@pytest.fixture(scope="module")
def rendered():
    return P.render()


@pytest.fixture(scope="module")
def context():
    return P.read_context()


def graph_of(files):
    return {e["@id"]: e for e in json.loads(files[canonical.DESCRIPTOR])["@graph"]}


def mutated(files, edit):
    """The files with the metadata edited: edit(graph by id, the whole document) in place."""
    out = dict(files)
    md = json.loads(files[canonical.DESCRIPTOR])
    by_id = {e["@id"]: e for e in md["@graph"]}
    edit(by_id, md)
    out[canonical.DESCRIPTOR] = canonical.dumps(md)
    return out


def problems(files, context):
    return P.check_profile_crate(files, context)


# -- what is made ----------------------------------------------------------------------------------------------------------------
def test_the_files_are_these_and_the_context_is_p0s_and_not_made_here(rendered):
    assert sorted(rendered) == sorted([
        "EXAMPLES.md", "README.md", "ro-crate-metadata.json", "validator/qro-crate/profile.ttl",
        "validator/qro-crate/must/1_structure.ttl", "validator/qro-crate/must/2_terms.ttl",
        "validator/qro-crate/must/3_domains.ttl", "validator/qro-crate/should/1_absence.ttl",
        "examples/fixture/ro-crate-metadata.json", "examples/fixture/data/notes.txt",
        "examples/fixture/data/raw.counts.json"])
    assert P.CONTEXT not in rendered and (PROFILE / P.CONTEXT).is_file()


def test_every_file_is_ascii_with_lf_line_ends_and_no_other_control_character(rendered):
    for path, data in rendered.items():
        assert all(b < 127 and (b >= 32 or b in (9, 10)) for b in data), path
        assert b"\r" not in data and (data.endswith(b"\n") or path.endswith("raw.counts.json")), path
    assert b"\t" not in b"".join(v for k, v in rendered.items() if k.endswith((".ttl", ".md")))


def test_the_files_on_disk_are_what_the_generator_renders_and_nothing_else_is_there(rendered):
    on_disk = {p.relative_to(PROFILE).as_posix(): p.read_bytes() for p in PROFILE.rglob("*") if p.is_file()}
    assert on_disk == {**rendered, P.CONTEXT: (PROFILE / P.CONTEXT).read_bytes()}


def test_no_python_is_under_profile_and_no_file_is_a_link():
    assert list(PROFILE.rglob("*.py")) == [] and not any(p.is_symlink() for p in PROFILE.rglob("*"))


def test_the_fixture_copy_is_the_fixture_and_the_checker_accepts_it_with_fixtures(rendered, tmp_path, monkeypatch):
    prepare(monkeypatch)
    for rel, data in rendered.items():
        if rel.startswith(P.FIXTURE_DIR):
            target = tmp_path / "crate" / rel[len(P.FIXTURE_DIR):]
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
    assert X.checker_verdict(tmp_path / "crate") == "accepted"
    again = fixture.make(tmp_path / "again")
    assert {p.relative_to(again).as_posix(): p.read_bytes() for p in again.rglob("*") if p.is_file()} == {
        rel[len(P.FIXTURE_DIR):]: data for rel, data in rendered.items() if rel.startswith(P.FIXTURE_DIR)}


def test_the_shapes_files_are_the_writers_text_of_the_generators_groups(rendered):
    from qro import p4_turtle
    for path, shapes in H.groups(widen=True).items():          # the claims published are the widened ones
        assert rendered[P.VALIDATOR + path] == p4_turtle.render(shapes, H.prefixes(), P.banner(path, shapes)).encode()
        assert turtle_problems(rendered[P.VALIDATOR + path].decode()) == []
    assert turtle_problems(rendered[P.VALIDATOR + "profile.ttl"].decode()) == []


def test_the_rocrate_validator_profile_names_this_profile_its_token_and_what_it_is_a_profile_of(rendered):
    text = rendered[P.VALIDATOR + "profile.ttl"].decode()
    assert f"<{V.PROFILE}> a prof:Profile ;" in text and f'prof:hasToken "{P.TOKEN}"' in text
    assert f"prof:isProfileOf <{V.ROCRATE}>" in text and f'rdfs:label "QRO-Crate {V.PROFILE_VERSION}"' in text
    assert P.TOKEN == "qro-crate" and P.VALIDATOR == "validator/qro-crate/"


# -- the Profile Crate's metadata ------------------------------------------------------------------------------------------------------
def test_the_metadata_is_canonical_bytes_in_the_qro_order(rendered):
    data = rendered[canonical.DESCRIPTOR]
    md = json.loads(data)
    assert canonical.dumps(md) == data and md["@context"] == V.context()          # RO-Crate 1.3's, and the qro prefix
    ids = [e["@id"] for e in md["@graph"]]
    assert ids[:2] == [canonical.DESCRIPTOR, V.PROFILE] and ids[2:] == sorted(ids[2:]) and len(ids) == len(set(ids))


def test_the_root_is_a_dataset_and_a_profile_with_what_rocrate_asks_and_the_tables_version(rendered):
    root = graph_of(rendered)[V.PROFILE]
    assert root["@type"] == ["Dataset", "Profile"] and root["name"] == V.PROFILE_NAME
    assert root["version"] == V.PROFILE_VERSION and root["datePublished"] == P.DATE_PUBLISHED
    assert root["license"] == {"@id": P.LICENSE} and root["isProfileOf"] == {"@id": V.ROCRATE}
    assert root["description"] and "identifier" not in root
    assert [x["@id"] for x in root["hasPart"]] == sorted(
        ["README.md", "EXAMPLES.md", "context.jsonld", "validator/qro-crate/", "examples/fixture/"])
    assert [x["@id"] for x in root["hasResource"]] == [
        "#hasContext", "#hasExamples", "#hasShapes", "#hasSpecification", "#hasVocabulary", "#shouldConformToProcessRun"]
    desc = graph_of(rendered)[canonical.DESCRIPTOR]
    assert desc == {"@id": canonical.DESCRIPTOR, "@type": "CreativeWork", "about": {"@id": V.PROFILE},
                    "conformsTo": {"@id": V.ROCRATE}}


def test_every_key_and_type_of_the_profile_crate_is_a_term_of_rocrates_context_so_that_json_ld_drops_nothing(rendered):
    from qro import p4_expand
    context = p4_expand.context()
    keys, types = set(), set()
    for e in json.loads(rendered[canonical.DESCRIPTOR])["@graph"]:
        for k, v in e.items():
            if k == "@type":
                types |= set(v if isinstance(v, list) else [v])
            elif k != "@id":
                keys.add(k)
    assert {k for k in keys if k not in context} == set() and {t for t in types if t not in context} == set()
    assert {"hasResource", "hasRole", "hasArtifact", "isProfileOf", "ResourceDescriptor", "Profile"} <= keys | types


def test_each_resource_has_the_role_and_the_artifact_it_should(rendered):
    g = graph_of(rendered)
    role = P.ROLE
    shapes = [{"@id": p} for p in sorted(rendered) if p.startswith(P.VALIDATOR)]
    examples = [{"@id": p} for p in sorted(["EXAMPLES.md"] + [q for q in rendered if q.startswith(P.FIXTURE_DIR)])]
    want = {"#hasSpecification": (role + "specification", [{"@id": "README.md"}]),
            "#hasContext": (role + "vocabulary", {"@id": P.CONTEXT_IRI}),
            "#hasVocabulary": (role + "vocabulary", {"@id": V.NAMESPACE}),
            "#hasShapes": (role + "validation", shapes),
            "#hasExamples": (role + "example", examples),
            "#shouldConformToProcessRun": (P.DCT_CONFORMS, {"@id": V.PROCESS_RUN_CRATE})}
    for i, (r, artifact) in want.items():
        assert g[i]["@type"] == "ResourceDescriptor" and g[i]["hasRole"] == {"@id": r}, i
        if isinstance(artifact, list) and len(artifact) == 1:
            artifact = artifact[0]
        assert g[i]["hasArtifact"] == artifact, i


def test_the_description_is_a_file_about_the_root_the_root_lists_and_names_its_media_type(rendered):
    d = graph_of(rendered)["README.md"]
    assert d["@type"] == "File" and d["about"] == {"@id": V.PROFILE} and d["encodingFormat"] == "text/markdown"
    assert {"@id": "README.md"} in graph_of(rendered)[V.PROFILE]["hasPart"]


def test_each_file_is_a_file_with_its_digest_its_size_and_a_media_type(rendered, context):
    g = graph_of(rendered)
    data = {**{k: v for k, v in rendered.items() if k != canonical.DESCRIPTOR}, P.CONTEXT: context}
    files = [e for e in g.values() if e["@type"] == "File"]
    assert sorted(e["@id"] for e in files) == sorted(data) and len(files) == len(rendered)
    for e in files:
        assert e["sha256"] == hashlib.sha256(data[e["@id"]]).hexdigest(), e["@id"]       # not P.sha: it must be held by another
        assert e["contentSize"] == str(len(data[e["@id"]])), e["@id"]
        assert e["encodingFormat"] == P.MEDIA[Path(e["@id"]).suffix] and e["description"], e["@id"]
    assert g["validator/qro-crate/"]["hasPart"] == [{"@id": p} for p in sorted(rendered) if p.startswith(P.VALIDATOR)]
    assert g["examples/fixture/"]["hasPart"] == [{"@id": p} for p in sorted(rendered) if p.startswith(P.FIXTURE_DIR)]


def test_the_contextual_profile_entities_are_rocrate_1_3_and_the_tables_process_run_crate(rendered):
    g = graph_of(rendered)
    assert g[V.ROCRATE] == {"@id": V.ROCRATE, "@type": ["CreativeWork", "Profile"], "name": "RO-Crate Metadata Specification",
                            "version": "1.3"}
    prc = next(e for e in V.profile_entities() if e["@id"] == V.PROCESS_RUN_CRATE)
    assert g[V.PROCESS_RUN_CRATE] == dict(prc, encodingFormat="text/html")       # the table's, and the page's media type
    assert g[P.LICENSE]["@type"] == "CreativeWork" and g[P.LICENSE]["name"] == "CC BY 4.0"


def test_the_vocabulary_is_written_once_as_a_defined_term_for_each_qro_term_and_type(rendered):
    g = graph_of(rendered)
    terms = [e for e in g.values() if e["@type"] == "DefinedTerm" and e.get("inDefinedTermSet") == {"@id": V.NAMESPACE}]
    want = [(t.key, t.meaning) for t in V.TERMS] + [(y.key, y.meaning) for y in V.TYPES]
    want = [(k, m) for k, m in want if k.startswith("qro:")]
    assert len(terms) == len(want) >= 50
    for key, meaning in want:
        e = g[V.NAMESPACE + key[4:]]
        assert (e["name"], e["termCode"], e["description"], e["inDefinedTermSet"]) == (key, key[4:], meaning,
                                                                                     {"@id": V.NAMESPACE})
    assert g[V.NAMESPACE] == {"@id": V.NAMESPACE, "@type": "DefinedTermSet", "name": "the QRO-Crate vocabulary",
                              "url": V.NAMESPACE.rstrip("#"), "encodingFormat": "text/html"}


def test_no_address_key_or_home_path_is_in_any_file(rendered, context):
    import importlib.util
    spec = importlib.util.spec_from_file_location("privacy_gate", ROOT / "tools" / "check_privacy.py")
    gate = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gate)
    for path, data in {**rendered, P.CONTEXT: context}.items():
        assert gate.findings(data.decode("ascii")) == [], path


# -- check_profile_crate: it holds the generated crate, and each rule of it is planted ----------------------------------------------------------
def test_the_generated_profile_crate_holds_what_rocrate_1_3_asks_of_one(rendered, context):
    assert problems(rendered, context) == []


def drop(i, key):
    return lambda g, md: g[i].pop(key)


def put(i, key, value):
    return lambda g, md: g[i].__setitem__(key, value)


PLANTS = [
    ("a root without a name", drop(V.PROFILE, "name"), "the root has no name"),
    ("a root without a description", drop(V.PROFILE, "description"), "the root has no description"),
    ("a root without a license", drop(V.PROFILE, "license"), "the root has no license"),
    ("a root without a datePublished", drop(V.PROFILE, "datePublished"), "the root has no datePublished"),
    ("a root without a version", drop(V.PROFILE, "version"), "the root has no version"),
    ("a root without isProfileOf", drop(V.PROFILE, "isProfileOf"), "the root has no isProfileOf"),
    ("a root without hasPart", drop(V.PROFILE, "hasPart"), "the root has no hasPart"),
    ("a root that is no Profile", put(V.PROFILE, "@type", "Dataset"), "typed Dataset and Profile"),
    ("a root that is no Dataset", put(V.PROFILE, "@type", ["CreativeWork", "Profile"]), "typed Dataset and Profile"),
    ("a root whose id is not an absolute IRI",
     lambda g, md: (g[V.PROFILE].__setitem__("@id", "./"), g[canonical.DESCRIPTOR].__setitem__("about", {"@id": "./"})),
     "the root's @id is an absolute IRI"),
    ("a datePublished that is no date", put(V.PROFILE, "datePublished", "yesterday"), "datePublished is an ISO date"),
    ("a datePublished in month 13", put(V.PROFILE, "datePublished", "2026-13-01"), "datePublished is an ISO date"),
    ("another version than the profile's", put(V.PROFILE, "version", "0.2"), "version is the profile's"),
    ("a profile of another RO-Crate", put(V.PROFILE, "isProfileOf", {"@id": "https://w3id.org/ro/crate/1.2"}),
     "a profile of RO-Crate 1.3"),
    ("a description not about the root", put("README.md", "about", {"@id": "#elsewhere"}), "the human-readable description"),
    ("a description without a media type", drop("README.md", "encodingFormat"), "the description names its encodingFormat"),
    ("a description that is no File", put("README.md", "@type", "CreativeWork"), "the human-readable description"),
    ("a root that does not list the description",
     lambda g, md: g[V.PROFILE].__setitem__("hasPart", [x for x in g[V.PROFILE]["hasPart"] if x["@id"] != "README.md"]),
     "the human-readable description"),
    ("a role outside the eight and conformsTo", put("#hasShapes", "hasRole", {"@id": "http://www.w3.org/ns/dx/prof/role/nonesuch"}),
     "a role among W3C's eight"),
    ("two roles", put("#hasShapes", "hasRole", [{"@id": P.ROLE + "validation"}, {"@id": P.ROLE + "example"}]),
     "a role among W3C's eight"),
    ("a resource without an artifact", drop("#hasShapes", "hasArtifact"), "names an artifact"),
    ("an artifact that is no entity", put("#hasShapes", "hasArtifact", {"@id": "validator/elsewhere/"}),
     "is no entity of the crate"),
    ("a resource that is no ResourceDescriptor", put("#hasShapes", "@type", "CreativeWork"), "names a ResourceDescriptor"),
    ("a recommended profile without its entity",
     lambda g, md: md["@graph"].remove(g[V.PROCESS_RUN_CRATE]), "has its contextual Profile entity"),
    ("a profile the root is of, without its entity", lambda g, md: md["@graph"].remove(g[V.ROCRATE]),
     "a profile named has a contextual Profile entity"),
    ("a hasResource that names nothing", put(V.PROFILE, "hasResource", [{"@id": "#nonesuch"}]), "names #nonesuch"),
    ("a contextual profile entity that is a Dataset too, which is another crate's root", put(V.ROCRATE, "@type", ["Dataset", "Profile"]),
     "a profile named has a contextual Profile entity"),
    ("a license the graph does not hold", put(V.PROFILE, "license", {"@id": "https://example.org/no-licence"}),
     "the root names https://example.org/no-licence"),
    ("a profile the root is of, which the graph does not hold", lambda g, md: md["@graph"].remove(g[V.ROCRATE]),
     "the root names " + V.ROCRATE),
    ("a file the root's hasPart does not reach",
     lambda g, md: g[V.PROFILE].__setitem__("hasPart", [x for x in g[V.PROFILE]["hasPart"] if x["@id"] != "EXAMPLES.md"]),
     "EXAMPLES.md: a data entity the root does not reach"),
    ("a file only a Dataset the root does not list reaches",
     lambda g, md: g[V.PROFILE].__setitem__("hasPart", [x for x in g[V.PROFILE]["hasPart"] if x["@id"] != "validator/qro-crate/"]),
     "validator/qro-crate/profile.ttl: a data entity the root does not reach"),
    ("a Dataset the root does not list",
     lambda g, md: g[V.PROFILE].__setitem__("hasPart", [x for x in g[V.PROFILE]["hasPart"] if x["@id"] != "validator/qro-crate/"]),
     "validator/qro-crate/: a data entity the root does not reach"),
    ("a hasPart of the root that names nothing",
     lambda g, md: g[V.PROFILE].__setitem__("hasPart", g[V.PROFILE]["hasPart"] + [{"@id": "gone.md"}]),
     "the root names gone.md"),
    ("a File with another digest", put("README.md", "sha256", "0" * 64), "the digest or the size is not the file's"),
    ("a File with another size", put("README.md", "contentSize", "1"), "the digest or the size is not the file's"),
    ("a File without a media type", drop("EXAMPLES.md", "encodingFormat"), "a File names its encodingFormat"),
    ("a Dataset that lists a file the graph lacks",
     lambda g, md: g["validator/qro-crate/"].__setitem__("hasPart", g["validator/qro-crate/"]["hasPart"] + [{"@id": "x.ttl"}]),
     "lists x.ttl"),
    ("a DefinedTerm gone", lambda g, md: md["@graph"].remove(g[V.NAMESPACE + "shots"]), "no more and no fewer"),
    ("a DefinedTerm too many", lambda g, md: md["@graph"].append({"@id": V.NAMESPACE + "extra", "@type": "DefinedTerm",
                                                                   "inDefinedTermSet": {"@id": V.NAMESPACE}}),
     "no more and no fewer"),
    ("a descriptor of another RO-Crate", put(canonical.DESCRIPTOR, "conformsTo", {"@id": "https://w3id.org/ro/crate/1.2"}),
     "conformsTo RO-Crate 1.3"),
    ("a descriptor that is a Dataset", put(canonical.DESCRIPTOR, "@type", "Dataset"), "a CreativeWork that conformsTo"),
    ("a descriptor about nothing", drop(canonical.DESCRIPTOR, "about"), "about one entity"),
    ("a descriptor about two entities",
     put(canonical.DESCRIPTOR, "about", [{"@id": V.PROFILE}, {"@id": "README.md"}]), "about one entity"),
    ("a descriptor about an entity the graph lacks", put(canonical.DESCRIPTOR, "about", {"@id": "#nowhere"}), "about one entity"),
    # what the check cannot read it refuses, by a name
    ("an entity that is no object", lambda g, md: md["@graph"].append(5), "an entity is an object with an @id that is a string"),
    ("an entity whose @id is a list", lambda g, md: g[V.PROFILE].__setitem__("@id", ["x"]),
     "an entity is an object with an @id that is a string"),
    ("a hasPart that holds a plain string", put(V.PROFILE, "hasPart", ["README.md"]), "hasPart holds a value that is no reference"),
    ("a license that is a reference and more", put(V.PROFILE, "license", {"@id": P.LICENSE, "name": "x"}),
     "license holds a value that is no reference"),
    ("an artifact that is a number", put("#hasSpecification", "hasArtifact", {"@id": 5}), "hasArtifact holds a value that is no reference"),
    # RO-Crate 1.3's profiles page
    ("an artifact with no encodingFormat", drop(V.NAMESPACE, "encodingFormat"), "declares its encodingFormat"),
    ("a recommended profile with no encodingFormat", drop(V.PROCESS_RUN_CRATE, "encodingFormat"), "declares its encodingFormat"),
    ("a JSON-LD context whose @id is a path", put("context.jsonld", "conformsTo", {"@id": P.JSONLD_CONTEXT}),
     "an entity that represents a JSON-LD context has an absolute @id"),
    ("a JSON-LD context in another media type", put(P.CONTEXT_IRI, "encodingFormat", "application/json"),
     "has the encodingFormat application/ld+json"),
    ("no entity that conforms to JSON-LD's Context", drop(P.CONTEXT_IRI, "conformsTo"),
     "has its entity, which conforms to JSON-LD's Context"),
    ("an @context without the qro prefix", lambda g, md: md.__setitem__("@context", P.CONTEXT_URL),
     "the metadata is an @context of RO-Crate 1.3's and the qro prefix"),
]


@pytest.mark.parametrize("why, edit, text", PLANTS, ids=[p[0] for p in PLANTS])
def test_each_rule_of_the_check_is_watched_failing(rendered, context, why, edit, text):
    found = problems(mutated(rendered, edit), context)
    assert found and any(text in f for f in found), (text, found)


def test_the_check_raises_on_nothing_and_never_needs_its_net_over_2000_random_edits(rendered, context):
    """P4's verifier, round 1, defect 3: 2,724 of 20,000 edits made the check raise, and the tool then said exit 3. The
    same fuzz with 20,000 edits is in tests/p4shacl/test_p4shacl_sweeps.py, where its cost (about 13 s) fits; this one costs
    about 1.3 s. Edits of the metadata (a value, a key, an entity, the order, the context), of the files beside it, and a
    dozen raw byte strings for the metadata, among them two nested 100,000 deep."""
    from p4_pcfuzz import run
    r = run(2000, seed=9, files=rendered, context=context)
    assert r["raised"] == {} and r["net"] == 0 and r["not_problems"] == 0, r
    assert r["clean"] + r["refused"] == 2000 and r["refused"] > 1200 and r["clean"] > 100      # it refuses much, and not all
    assert r["raw"] >= 30 and r["files"] >= 200 and r["edited"] >= 3000                         # and the fuzz tried what it says


def test_the_fuzz_hands_out_copies_of_its_values_and_never_changes_its_pool(rendered, context):
    """A value shared between edits is changed by the next edit, and then two edits make a cycle (the first draft's
    "Circular reference detected", found by the 20,000-edit run and not by a short one)."""
    import random
    from p4_pcfuzz import VALUES, run, value
    before = copy.deepcopy(VALUES)
    rnd = random.Random(1)
    drawn = [value(rnd) for _ in range(400)]
    assert sum(isinstance(v, (list, dict)) for v in drawn) > 100
    for v in drawn:
        if isinstance(v, (list, dict)):
            assert all(v is not x for x in VALUES)
    run(300, seed=4, files=rendered, context=context)
    assert VALUES == before


def test_the_fuzz_finds_a_check_that_raises_or_needs_its_net(rendered, context, monkeypatch):
    from p4_pcfuzz import run
    real = P._check

    def raises_on_a_list_id(files, context_bytes):
        md = json.loads(files[canonical.DESCRIPTOR])
        if isinstance(md, dict) and isinstance(md.get("@graph"), list) and any(
                isinstance(e, dict) and isinstance(e.get("@id"), list) for e in md["@graph"]):
            return {e.get("@id"): e for e in md["@graph"]}          # TypeError: unhashable type
        return real(files, context_bytes)
    monkeypatch.setattr(P, "_check", raises_on_a_list_id)
    r = run(400, seed=9, files=rendered, context=context)
    assert r["net"] > 0                                            # the net caught it, and the fuzz counts it
    monkeypatch.setattr(P, "check_profile_crate", lambda files, context_bytes=None: raises_on_a_list_id(files, context_bytes))
    r = run(400, seed=9, files=rendered, context=context)
    assert sum(r["raised"].values()) > 0 or r["not_problems"] > 0     # and a check without the net would be seen to raise


def graph_with(files, bad):
    """Whether the metadata parses and its @graph holds an item for which `bad` is true."""
    try:
        md = json.loads(files[canonical.DESCRIPTOR])
    except (KeyError, TypeError, ValueError, RecursionError):
        return False
    return isinstance(md, dict) and isinstance(md.get("@graph"), list) and any(bad(e) for e in md["@graph"])


def one_id_two_types(files):
    """Whether two entities of the @graph have one @id and are not alike: an id that is another's, not a copy of an entity."""
    try:
        graph = json.loads(files[canonical.DESCRIPTOR]).get("@graph")
    except (KeyError, TypeError, ValueError, RecursionError, AttributeError):
        return False
    seen = {}
    for e in graph if isinstance(graph, list) else []:
        if isinstance(e, dict) and isinstance(e.get("@id"), str):
            seen.setdefault(e["@id"], set()).add(json.dumps(e.get("@type"), sort_keys=True))
    return any(len(types) > 1 for types in seen.values())


KINDS = {             # the kinds of input the fuzz says it makes, each as a test of the files the check is given
    "an entity whose id is another entity's": one_id_two_types,
    "a key that is no path": lambda files: any(not isinstance(k, str) for k in files),
    "a metadata file that is no bytes": lambda files: not isinstance(files.get(canonical.DESCRIPTOR), (bytes, bytearray)),
    "a metadata file 100,000 deep": lambda files: isinstance(files.get(canonical.DESCRIPTOR), bytes) and files[
        canonical.DESCRIPTOR][:1000].count(b"[") > 900,
    "an entity that is no object": lambda files: graph_with(files, lambda e: not isinstance(e, dict)),
    "an entity whose id is not a string": lambda files: graph_with(files, lambda e: isinstance(e, dict) and not isinstance(
        e.get("@id"), str)),
    "a file's content that is text": lambda files: any(isinstance(v, str) for k, v in files.items() if k != canonical.DESCRIPTOR),
}


def test_the_fuzz_makes_each_kind_of_input_it_says(rendered, context, monkeypatch):
    """The detection of a check that raises is the test above; this one holds that the inputs it would raise on are made."""
    from p4_pcfuzz import run
    real = P._check
    seen = dict.fromkeys(KINDS, 0)

    def spy(files, context_bytes):
        for why, kind in KINDS.items():
            seen[why] += bool(kind(files))
        return real(files, context_bytes)
    monkeypatch.setattr(P, "_check", spy)
    run(800, seed=9, files=rendered, context=context)
    assert [why for why, n in seen.items() if n == 0] == [], seen


def test_the_fuzz_finds_a_check_that_names_one_problem_twice(rendered, context, monkeypatch):
    from p4_pcfuzz import run
    real = P._check
    monkeypatch.setattr(P, "_check", lambda files, context_bytes: real(files, context_bytes) * 2)
    assert run(300, seed=9, files=rendered, context=context)["not_problems"] > 100


def test_a_bug_of_the_check_shows_as_the_nets_problem_and_not_as_a_crash(rendered, context, monkeypatch):
    monkeypatch.setattr(P, "_check", lambda files, context_bytes: 1 / 0)
    assert P.check_profile_crate(rendered, context) == [f"{P.NET}: ZeroDivisionError"]


@pytest.mark.parametrize("signal", [KeyboardInterrupt, SystemExit])
def test_the_net_catches_a_bug_of_the_check_and_never_a_request_to_stop(rendered, context, monkeypatch, signal):
    def stop(files, context_bytes):
        raise signal()
    monkeypatch.setattr(P, "_check", stop)
    with pytest.raises(signal):
        P.check_profile_crate(rendered, context)


def test_a_file_may_be_any_bytes_and_a_key_that_is_no_path_is_no_file(rendered, context):
    assert problems({**rendered, "README.md": bytearray(rendered["README.md"])}, context) == []
    assert problems({**rendered, 5: b"x", None: b"y", ("a", "b"): b"z"}, context) == []
    found = problems({**rendered, "README.md": "text, not bytes"}, context)
    assert found == ["README.md: a file that is no bytes"]


@pytest.mark.parametrize("bad", [5, None, ["x"], {"a": 1}, "text", 1.5, True])
def test_a_metadata_file_that_is_no_bytes_is_a_named_problem(rendered, context, bad):
    found = problems({**rendered, canonical.DESCRIPTOR: bad}, context)
    assert len(found) == 1 and found[0].startswith("the Profile Crate's metadata is not readable: "), found
    assert P.NET not in found[0]


def test_a_problem_is_named_once_however_many_rules_read_the_value(rendered, context):
    twice = mutated(rendered, put(V.PROFILE, "hasPart", [{"@id": 5}, {"@id": "README.md"}, {"x": 1}]))
    found = problems(twice, context)
    assert len(found) == len(set(found)) and any("holds a value that is no reference" in f for f in found), found


def test_the_two_readers_of_the_check_take_what_is_a_string_and_nothing_else():
    """`types_of` and `named` are what every rule asks first; they are called with whatever the metadata holds."""
    assert P.types_of({"@type": "File"}) == ["File"] and P.types_of({"@type": ["File", "Dataset"]}) == ["File", "Dataset"]
    assert P.types_of({"@type": ["File", 5, None, ["x"], {}]}) == ["File"]                 # an item that is no string names no type
    assert P.types_of({"@type": 5}) == [] and P.types_of({"@type": None}) == [] and P.types_of({}) == []
    assert P.types_of(None) == [] and P.types_of("File") == [] and P.types_of([{"@type": "File"}]) == []      # and no entity is no object
    assert P.named("x") and not P.named("") and not P.named(5) and not P.named(None) and not P.named(["x"]) and not P.named({})


def test_a_rule_on_the_simplest_plants_names_exactly_one_problem(rendered, context):
    for edit, text in ((drop(V.PROFILE, "name"), "the root has no name"), (put(V.PROFILE, "version", "0.2"),
                                                                           "version is the profile's"),
                       (put("README.md", "sha256", "0" * 64), "the digest or the size")):
        found = problems(mutated(rendered, edit), context)
        assert len(found) == 1 and text in found[0], found


def test_the_check_names_the_files_and_the_metadata_that_disagree(rendered, context):
    gone = {k: v for k, v in rendered.items() if k != "EXAMPLES.md"}
    assert any("EXAMPLES.md: a File whose file is not there" in f for f in problems(gone, context))
    extra = dict(rendered, **{"validator/qro-crate/extra.ttl": b"x"})
    assert problems(extra, context) == ["validator/qro-crate/extra.ttl: a file no entity lists"]
    changed = dict(rendered, **{"EXAMPLES.md": rendered["EXAMPLES.md"] + b"x"})
    assert problems(changed, context) == ["EXAMPLES.md: the digest or the size is not the file's"]
    assert any("context.jsonld" in f for f in problems(rendered, context + b" "))


def test_the_check_is_not_confused_by_what_is_not_json_or_not_a_profile_crate(rendered, context):
    assert problems({**rendered, canonical.DESCRIPTOR: b"{"}, context) == ["the Profile Crate's metadata is not readable: "
                                                                          "JSONDecodeError"]
    missing = {k: v for k, v in rendered.items() if k != canonical.DESCRIPTOR}
    assert problems(missing, context)[0].startswith("the Profile Crate's metadata is not readable")
    for md in ({"@context": "x", "@graph": []}, {"@context": V.context()}, {"@graph": []}, [], {"@context": V.context(),
                                                                                                 "@graph": "x"},
               {"@context": P.CONTEXT_URL, "@graph": []}):                    # RO-Crate's alone, without the qro prefix
        assert problems({canonical.DESCRIPTOR: json.dumps(md).encode()}, context) == [
            "the metadata is an @context of RO-Crate 1.3's and the qro prefix, and an @graph"]
    twice = mutated(rendered, lambda g, md: md["@graph"].append(copy.deepcopy(md["@graph"][2])))
    assert any("an entity twice" in f for f in problems(twice, context))
    noid = mutated(rendered, lambda g, md: md["@graph"].append({"@id": "#x", "@type": "CreativeWork"}))
    assert problems(noid, context) == []


# -- the README and the matrix ------------------------------------------------------------------------------------------------------------------
def anchors(text):
    return re.findall(r'<a id="([^"]+)"></a>', text)


def test_the_readme_has_an_anchor_for_each_shape_and_for_the_two_annotations_and_for_nothing_else(rendered):
    text = rendered[P.DESCRIPTION].decode()
    got = anchors(text)
    ids = [X.local(s.id) for s in H.build()]
    assert sorted(got) == sorted(ids + ["claims", "kind"]) and len(got) == len(set(got))
    for s in H.build():
        row = next(ln for ln in text.splitlines() if f'<a id="{X.local(s.id)}"></a>' in ln)
        assert f" {s.level} " in row and s.name in row.replace("\\|", "|")
        assert row.endswith(f"| {', '.join(s.claims) or 'none'} |"), s.id          # and the claims on the page are the published ones


def test_the_readme_states_the_levels_the_shapes_and_the_limits_from_the_table_and_the_code(rendered):
    text = rendered[P.DESCRIPTION].decode()
    must = sum(s.level == "must" for s in H.build())
    should = sum(s.level == "should" for s in H.build())
    assert f"{len(H.build())} shapes: {must} must and {should} should." in text
    assert "| must | `validator/qro-crate/must/` | Violation | " in text and f"| {must} |" in text
    for i, (title, body) in enumerate(P.LIMITS, 1):
        assert f"{i}. **{title}**" in text
    assert text.count("\n1. **") == 1 and f"\n{len(P.LIMITS)}. **" in text
    for e in V.profile_entities():
        assert e["@id"] in text and e["version"] in text
    assert V.PROFILE_VERSION in text.splitlines()[2] and P.DATE_PUBLISHED in text
    assert "provisional" in text and "CC BY 4.0" in text


def test_the_relative_links_of_the_readme_and_the_matrix_resolve(rendered):
    for name in (P.DESCRIPTION, P.EXAMPLES):
        for target in re.findall(r"\[[^\]]*\]\(([^)#\s]+)(?:#[^)]*)?\)", rendered[name].decode()):
            if "://" in target:
                continue
            assert (PROFILE / target).resolve().exists(), (name, target)


def test_the_matrix_lists_each_written_plant_once_and_counts_the_ones_the_table_makes(rendered):
    text = rendered[P.EXAMPLES].decode()
    for p in X.PLANTS:
        assert len(re.findall(rf"^\| `{re.escape(p.name)}` \|", text, re.M)) == 1, p.name
    assert not re.search(r"^\| `(spell|domain|many)-", text, re.M)
    assert f"## Plants ({len(X.PLANTS)} written, {len(X.generated())} made from the table)" in text
    heads = re.findall(r"^### (\w[\w ]*)$", text, re.M)
    assert [h for h in heads if h in X.FAMILIES] == [f for f in X.FAMILIES if any(p.family == f for p in X.PLANTS)]
    rows = re.findall(r"^\| `[^`]+` \|.*accepted but for step 9", text, re.M)
    assert len(rows) == sum(p.checker == X.GENERATED for p in X.PLANTS) >= 14 and "step-unbuilt" in text
    for p in X.PLANTS:                                  # an abstaining plant says what a real engine does with it, and that the checker refuses it
        if p.unreadable:
            row = next(ln for ln in text.splitlines() if ln.startswith(f"| `{p.name}` |"))
            assert f"| {p.checker} | the evaluator abstains; pyshacl fails {', '.join(p.engine) or 'no must shape'} |" in row, p.name
            assert p.checker in V.REFUSAL, p.name                 # the checker refuses the crate, by a name
    assert sum(p.unreadable for p in X.PLANTS) == 6


def test_a_non_ascii_character_in_markdown_is_a_numeric_reference_never_a_byte():
    assert P.ascii_md("café 中") == "caf&#233; &#20013;" and P.ascii_md("plain") == "plain"
    assert P.cell("a|b\nc") == "a\\|b c"


def test_a_render_without_p0s_context_says_so(tmp_path):
    with pytest.raises(P.ContextMissing, match="gen_vocabulary.py --write"):
        P.render(tmp_path)
    (tmp_path / "profile").mkdir()
    (tmp_path / "profile" / P.CONTEXT).write_bytes(b"{}\n")
    files = P.render(tmp_path)
    assert graph_of(files)[P.CONTEXT]["sha256"] == hashlib.sha256(b"{}\n").hexdigest()
    assert P.sha(b"abc") == "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"      # FIPS 180's own example


def test_the_stated_limits_are_the_one_list_the_readme_renders():
    assert len(P.LIMITS) >= 20 and all(title.endswith(".") and body for title, body in P.LIMITS)
    assert len({title for title, _ in P.LIMITS}) == len(P.LIMITS)


def test_the_limit_about_looser_spellings_names_each_kind_of_looseness_the_differential_finds():
    from p4_helpers import LOOSER
    text = next(body for title, body in P.LIMITS if title.startswith("Some spellings are looser"))
    kinds = {"2^63 - 1": "above 2^63", "lowest terms": "lowest terms", "1,000 digits": "1,000 digits",
             "exact": "decimal that is not", "not real": "not a real", "control character": "control character",
             "lone surrogate": "lone surrogate", "trailing line feed": "trailing line feed"}
    found = {why for why in LOOSER.values()}
    for key, fragment in kinds.items():
        assert any(fragment in why for why in found), (key, "no sample of it in LOOSER")
        assert key in text, key
    assert len(LOOSER) >= 22
    for spelling in sorted({sp for (sp, _), why in LOOSER.items() if "trailing line feed" in why}):
        assert spelling in text or f"an {spelling}" in text, (spelling, "the limit does not name it")


def test_the_limits_about_ids_name_the_base_the_plants_and_the_shapes_a_real_engine_fails_on_them():
    """Defect 1, after P0.5: limit 19 restated. It names the base of the engine stage, each shape a real engine fails on a crate
    the evaluator cannot read, and every plant the limits quote is a plant."""
    from qro import p4_expand
    text = next(body for title, body in P.LIMITS if title.startswith("An id is read at one base"))
    assert f"at the base `{p4_expand.BASE}`" in text and f"and at `{p4_expand.BASE}` no such IRI" in text
    assert "item 22" in text and "family `abstains`" in text
    assert "refuses an id outside the rule `spelling`, and a reference outside it `graph-form`, and every must shape claims both" in text
    plants = {p.name: p for p in X.PLANTS}
    engine = {shape for p in plants.values() if p.unreadable for shape in p.engine}
    assert engine == {"entity", "term-name", "file-digest-present", "term-haspart"}
    for shape in engine:
        assert f"`{shape}`" in text, shape
    quoted = set(re.findall(r"`(abstains-[a-z-]+)`", " ".join(body for _, body in P.LIMITS)))
    assert quoted and quoted <= set(plants) and all(plants[n].unreadable for n in quoted), quoted


def test_the_limit_about_a_remote_file_says_what_the_sweeps_measure_listed_and_unlisted():
    """The third verifier, D2, MEASURED: "A remote File carrying a sha256 conforms" held only where the root lists it. The checker
    refuses the crate `graph-form` either way (tests/p4/test_p4_sweeps.py holds both)."""
    text = next(body for title, body in P.LIMITS if title.startswith("A `local-file` is read as any `File`"))
    assert "carrying a sha256 is refused `graph-form` by the checker, whether or not the root lists it" in text
    assert "it conforms where the root lists it in `hasPart`, and fails `file-reached` where the root does not" in text
    assert "A remote File carrying a sha256 conforms." not in text


def test_every_place_that_describes_the_claims_says_every_must_shape_claims_the_six_refusals_of_form(rendered):
    """The lead's ruling of 2026-10-26T11:18:27Z (P4's verifier, round 2, defect 3): the README, the banner of every Turtle file,
    the matrix and the plant that found the first of them say that every must shape claims the six names of FORM, and the claims
    column of the README is the shapes' own (test_the_readme_has_an_anchor_for_each_shape)."""
    readme = rendered[P.DESCRIPTION].decode()
    six = ", ".join(f"`{n}`" for n in H.FORM[:-1]) + f" and `{H.FORM[-1]}`"
    assert f"every must shape adds the six refusals of steps 1 and 2 that can come before its own and that RDF cannot show: {six}" in readme
    assert "the two refusals of form" not in readme and "the two of form" not in readme       # the old words are gone
    assert "| Violation | the checker refuses the crate; one fault from an accepted crate, by a name a failing shape claims (limit 1) |" in readme
    files = [path for path in rendered if path.startswith(P.VALIDATOR) and path.endswith(".ttl") and ("/must/" in path or "/should/" in path)]
    assert len(files) >= 2
    for path in files:
        head = rendered[path].decode().split("\n@prefix", 1)[0].replace("\n# ", " ")
        assert ("then the six of steps 1 and 2 that can come before its own: " + ", ".join(H.FORM) + ". When a must shape fails") in head, path
        assert "then spelling and term-unknown, which can come first" not in head, path
    matrix = rendered[P.EXAMPLES].decode()
    assert "by a name the failing shape claims (limit 19: every must shape claims `spelling` and `graph-form`)" in matrix
    row = next(ln for ln in matrix.splitlines() if ln.startswith("| `abstains-blank-node-reference` |"))
    assert "every must shape claims the checker's `graph-form` (limit 19)" in row
    for s in H.build():                                 # and the claims column is the shapes' own, FORM's six on each must shape
        line = next(ln for ln in readme.splitlines() if ln.startswith("| ") and f'<a id="{X.local(s.id)}"></a>' in ln)
        assert line.endswith(f"| {', '.join(s.claims) or 'none'} |"), s.id
        assert (set(H.FORM) <= set(s.claims)) == (s.level == "must"), s.id


def test_the_limit_about_the_evaluator_and_pyshacl_names_the_three_things_and_what_the_shapes_and_the_crates_reach():
    """The lead's ruling of 2026-10-26T11:18:27Z, a note of P4's second verifier: a stated limit for the two constructs the
    evaluator and pyshacl read differently, which the generated shapes do not use; and the ruling of 18:56:48Z, a note of the
    fourth verifier: the integer lexical forms, a third, which no crate reaches."""
    title, text = P.LIMITS[-1]
    assert title == "The evaluator and pyshacl read three things differently, and none changes a verdict on a crate."
    assert len(P.LIMITS) == 23
    assert "`sh:minLength 0` on a blank node" in text and "`sh:maxInclusive` with no `sh:minInclusive`" in text
    assert "The generated shapes use neither: no `sh:minLength` is below 1 (`sh:maxLength` is used, with several bounds" in text
    assert "a length bound is only 1" not in text                    # the third verifier, D2: sh:maxLength takes five bounds
    assert "limit 23 names three things" in next(body for title, body in P.LIMITS if title.startswith("The shapes are held to one engine"))
    # the third: the six forms the ruling names, in the words it uses, and the three claims about them
    assert "The third is the lexical form of an integer." in text
    for named in ("`' 1'`", "`'1 '`", "a tab and a line feed around `1`", "`'1_0'`", "U+0661 and U+FF11"):
        assert named in text, named
    assert "the evaluator fails the shape" in text and "pyshacl accepts the literal" in text
    assert "rdflib 7.6.0 maps an integer's lexical form with Python's `int()` and calls a literal well formed when it has a value" in text
    assert "No crate reaches these forms." in text and "so the soundness of the shapes is untouched" in text
    # which judge is right: what the tree can say, what it cannot, and what is believed
    assert "the checker refuses all six forms, so pyshacl's reading is the looser" in text
    assert "which is right by XSD 1.1 and RDF 1.1 Concepts, since it pins no copy of either" in text
    assert "BELIEVED, from XSD 1.1's definition of the integer, recalled and not re-read" in text
    assert "on the three forms with white space it turns on whether XSD's collapse of white space applies" in text


def test_the_shapes_say_they_are_for_an_engine_run_without_inference_in_limit_2_and_in_every_banner_with_the_engine_stages_counts(rendered):
    """The ruling of 2026-10-26T18:56:48Z, the fourth verifier's most consequential note: pyshacl with rdfs, owlrl or both fails
    the accepted fixture crate, and no document said to run without inference. The counts are P.INFERENCE, which the engine stage
    holds (tests/p4shacl/test_p4shacl_inference.py), so the README and the banners quote the engine's."""
    counts = P.INFERENCE_COUNTS
    assert counts == "94, 112 and 527" and P.INFERENCE == {"rdfs": 94, "owlrl": 112, "both": 527}
    text = next(body for title, body in P.LIMITS if title.startswith("The shapes are held to one engine"))
    assert ("The shapes are for an engine run without inference: pyshacl's `inference` is `none`, its default, in the engine "
            "stage and wherever these shapes are used. With `rdfs`, `owlrl` or `both` it fails the accepted fixture crate") in text
    assert P.INFERENCE_SHAPES == ("descriptor", "entity", "profile-entities")
    assert f"on `descriptor`, `entity` and `profile-entities`, with {counts} results" in text
    assert text in rendered[P.DESCRIPTION].decode()                                         # and the README renders it
    files = [path for path in rendered if path.startswith(P.VALIDATOR) and path.endswith(".ttl") and ("/must/" in path or "/should/" in path)]
    assert len(files) >= 2
    for path in files:
        head = rendered[path].decode().split("\n@prefix", 1)[0].replace("\n# ", " ")
        assert ("Run an engine WITHOUT inference (pyshacl: inference=none, its default). With rdfs, owlrl or both it fails the "
                f"accepted fixture crate on descriptor, entity and profile-entities, with {counts} results (README, limit 2).") in head, path
    page = (ROOT / "docs" / "P4.md").read_text(encoding="utf-8")
    assert "without inference" in page and counts in page and "`descriptor`, `entity` and `profile-entities`" in page


def test_the_limit_about_extension_terms_names_the_codes_that_clash_and_the_context_maps_only_the_prefix(rendered):
    """P4's verifier, round 1, defect 4: the extension terms SHOULD be mapped in the Profile Crate's @context. The prefix is
    mapped (V.context()), and a bare code is not, where it is a term of RO-Crate's own context, which it would redefine."""
    from qro import p4_expand
    clash = sorted(t["termCode"] for t in P.defined_terms() if t["termCode"] in p4_expand.context())
    text = next(body for title, body in P.LIMITS if title.startswith("The extension terms are mapped by one prefix"))
    assert clash == ["Question", "device", "line", "value"], clash                # the table moves: this names the new one
    for code in clash:
        assert f"`{code}`" in text, code
    assert json.loads(rendered[canonical.DESCRIPTOR])["@context"] == V.context() and len(V.context()) == 2


def test_the_numbers_the_first_limit_quotes_are_the_sweeps():
    from p4_sweeps import alias_crates, edits, families
    text = next(body for title, body in P.LIMITS if title == "The checker is the authority.")
    readme = next(ln for ln in P.render()[P.DESCRIPTION].decode().splitlines() if ln.startswith("The shapes below are written"))
    work = X.Workspace()
    try:
        pool = len(edits(work.pristine))
        crates = len(alias_crates(work))
        more = len(families(work.pristine))
    finally:
        work.close()
    assert f"{pool:,}" in text and f"{crates} crates" in text and f"{more} crates of three families" in text, (pool, crates, more)
    assert f"{pool:,}" in readme and f"{crates} crates" in readme and f"{more} crates of three families" in readme


def test_the_context_has_an_entity_at_its_absolute_iri_and_its_local_copy_says_it_is_the_same_document(rendered):
    """P4's verifier, round 1, defect 4: RO-Crate 1.3 asks the entity that represents a JSON-LD context for an absolute @id and
    the encodingFormat application/ld+json; a file present in the crate keeps its relative path."""
    g = graph_of(rendered)
    e = g[P.CONTEXT_IRI]
    assert e["@type"] == "CreativeWork" and e["encodingFormat"] == "application/ld+json" and e["conformsTo"] == {"@id": P.JSONLD_CONTEXT}
    assert P.CONTEXT_IRI == P.RAW_HOME + "profile/context.jsonld" and P.CONTEXT_IRI.startswith("https://")
    assert g[P.JSONLD_CONTEXT]["@type"] == "DefinedTerm"
    local = g["context.jsonld"]
    assert local["@type"] == "File" and local["sameAs"] == {"@id": P.CONTEXT_IRI}
    assert {"@id": "context.jsonld"} in g[V.PROFILE]["hasPart"] and {"@id": P.CONTEXT_IRI} not in g[V.PROFILE]["hasPart"]


def test_every_artifact_of_a_resource_declares_its_encodingFormat(rendered):
    g = graph_of(rendered)
    seen = 0
    for e in g.values():
        if e["@type"] == "ResourceDescriptor":
            artifacts = e["hasArtifact"] if isinstance(e["hasArtifact"], list) else [e["hasArtifact"]]
            for a in artifacts:
                assert g[a["@id"]].get("encodingFormat"), (e["@id"], a["@id"])
                seen += 1
    assert seen == 13                                   # 1 + 1 + 1 + the 5 Turtle files + EXAMPLES.md and the 3 of the fixture + 1


def test_the_readme_dates_the_profile_and_does_not_say_it_is_published(rendered):
    text = rendered[P.DESCRIPTION].decode()
    assert "**Published" not in text and "a placeholder" in text and P.DATE_PUBLISHED in text
    assert f"**Version {V.PROFILE_VERSION}**" in text
