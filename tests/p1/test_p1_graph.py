"""The entity graph as steps 4, 5 and 8, and P2's step 6, read it: an Index over any metadata that has an "@graph".
A relation that is missing or holds twice is a GraphError, never a guess."""
import copy
import json

import pytest

from qro.p1_graph import GraphError, Index, ref_ids, types_of


def ref(i):
    return {"@id": i}


def graph():
    return {"@graph": [
        {"@id": "./", "@type": "Dataset"},
        {"@id": "run/raw.json", "@type": ["File", "qro:RawResult"], "sha256": "a" * 64},
        {"@id": "run/line.json", "@type": "File", "sha256": "b" * 64},
        {"@id": "run/twin.json", "@type": "File", "sha256": "b" * 64},
        {"@id": "run/nodigest.json", "@type": "File"},
        {"@id": "#pub-j-0", "@type": "qro:Pub"}, {"@id": "#pub-j-1", "@type": "qro:Pub"},
        {"@id": "#job-j", "@type": ["CreateAction", "qro:Job"], "object": [ref("#pub-j-0"), ref("#pub-j-1")],
         "result": [ref("run/raw.json"), ref("run/line.json"), ref("https://example.org/elsewhere")],
         "qro:device": ref("#device"), "qro:line": ref("run/line.json")},
        {"@id": "#decode-j", "@type": ["CreateAction", "qro:Decode"], "object": [ref("run/raw.json")]},
        {"@id": "#device", "@type": "IndividualProduct"}]}


def test_the_types_of_an_entity_are_a_list_whether_it_wrote_a_string_or_a_list():
    assert types_of({"@type": "File"}) == ["File"] and types_of({"@type": ["File", "x"]}) == ["File", "x"]
    assert types_of({}) == [] and types_of({"@type": 5}) == []


def test_ref_ids_are_the_ids_of_a_reference_or_a_list_of_them_and_nothing_else():
    assert ref_ids(ref("a")) == ["a"] and ref_ids([ref("a"), ref("b")]) == ["a", "b"]
    assert ref_ids(None) == [] and ref_ids("a") == [] and ref_ids([{"x": 1}, 7, ref("c")]) == ["c"]
    assert ref_ids({"@id": 5}) == []


def test_entities_are_found_by_id_and_by_type_in_the_graphs_order():
    idx = Index(graph())
    assert idx.by_id["#job-j"]["qro:device"] == ref("#device")
    assert [e["@id"] for e in idx.of_type("qro:Pub")] == ["#pub-j-0", "#pub-j-1"]
    assert [e["@id"] for e in idx.of_type("File")] == ["run/raw.json", "run/line.json", "run/twin.json",
                                                       "run/nodigest.json"]
    assert idx.of_type("qro:Job")[0]["@id"] == "#job-j" and idx.of_type("CreateAction")[0]["@id"] == "#job-j"
    assert idx.of_type("qro:Snapshot") == []


def test_of_type_returns_a_copy_so_a_caller_cannot_change_the_index():
    idx = Index(graph())
    idx.of_type("qro:Pub").clear()
    assert len(idx.of_type("qro:Pub")) == 2


def test_get_takes_an_id_or_a_reference_and_may_ask_for_a_type():
    idx = Index(graph())
    assert idx.get("#device")["@id"] == "#device" and idx.get(ref("#device"))["@id"] == "#device"
    assert idx.get("#pub-j-0", "qro:Pub")["@id"] == "#pub-j-0"
    with pytest.raises(GraphError, match="not a qro:Job"):
        idx.get("#pub-j-0", "qro:Job")
    for bad in ("#nowhere", ref("#nowhere"), 5, None, {"x": 1}):
        with pytest.raises(GraphError, match="names no entity"):
            idx.get(bad)


def test_refs_and_one_follow_a_term_to_the_entities_it_names():
    idx, job = Index(graph()), graph()["@graph"][7]
    assert idx.refs(job, "object") == ["#pub-j-0", "#pub-j-1"] and idx.refs(job, "missing") == []
    assert idx.one(job, "qro:device")["@id"] == "#device"
    assert idx.one(job, "qro:device", "IndividualProduct")["@id"] == "#device"
    with pytest.raises(GraphError, match="names 2 entities, not one"):
        idx.one(job, "object")
    with pytest.raises(GraphError, match="names 0 entities, not one"):
        idx.one(job, "instrument")
    with pytest.raises(GraphError, match="names no entity"):
        idx.one({"@id": "x", "t": ref("#nowhere")}, "t")


def test_refs_of_type_skips_what_is_not_there_or_not_of_the_type():
    idx, job = Index(graph()), graph()["@graph"][7]
    assert [e["@id"] for e in idx.refs_of_type(job, "result", "qro:RawResult")] == ["run/raw.json"]
    assert [e["@id"] for e in idx.refs_of_type(job, "result", "File")] == ["run/raw.json", "run/line.json"]
    assert idx.refs_of_type(job, "result", "qro:Pub") == []


def test_a_pubs_job_a_jobs_raw_result_and_a_raws_decode_are_found_by_what_names_them():
    idx = Index(graph())
    job = idx.job_of("#pub-j-1")
    assert job["@id"] == "#job-j" and idx.job_of(idx.by_id["#pub-j-0"]) is job
    raw = idx.raw_of(job)
    assert raw["@id"] == "run/raw.json"
    assert idx.decode_of(raw)["@id"] == "#decode-j" and idx.decode_of("run/raw.json")["@id"] == "#decode-j"
    assert idx.job_of_raw(raw)["@id"] == "#job-j" and idx.job_of_raw("run/raw.json")["@id"] == "#job-j"
    assert [p["@id"] for p in idx.pubs_of(job)] == ["#pub-j-0", "#pub-j-1"]


def test_a_relation_that_is_missing_or_held_twice_is_a_graph_error():
    def changed(fn):
        g = graph()
        fn({e["@id"]: e for e in g["@graph"]}, g["@graph"])
        return Index(g)
    with pytest.raises(GraphError, match="0 jobs list it"):
        changed(lambda by, g: by["#job-j"].pop("object")).job_of("#pub-j-0")
    two = changed(lambda by, g: g.append({"@id": "#job-k", "@type": "qro:Job", "object": [ref("#pub-j-0")]}))
    with pytest.raises(GraphError, match="2 jobs list it"):
        two.job_of("#pub-j-0")
    assert two.job_of("#pub-j-1")["@id"] == "#job-j"
    none = changed(lambda by, g: by["#job-j"].update({"result": [ref("run/line.json")]}))
    with pytest.raises(GraphError, match="0 raw results"):
        none.raw_of(none.by_id["#job-j"])
    twice = changed(lambda by, g: (g.append({"@id": "run/raw2.json", "@type": ["File", "qro:RawResult"]}),
                                   by["#job-j"].update({"result": [ref("run/raw.json"), ref("run/raw2.json")]})))
    with pytest.raises(GraphError, match="2 raw results"):
        twice.raw_of(twice.by_id["#job-j"])
    with pytest.raises(GraphError, match="0 decodes read it"):
        changed(lambda by, g: by["#decode-j"].pop("object")).decode_of("run/raw.json")
    two = changed(lambda by, g: g.append({"@id": "#decode-k", "@type": "qro:Decode", "object": [ref("run/raw.json")]}))
    with pytest.raises(GraphError, match="2 decodes read it"):
        two.decode_of("run/raw.json")
    with pytest.raises(GraphError, match="0 jobs made it"):
        changed(lambda by, g: by["#job-j"].update({"result": []})).job_of_raw("run/raw.json")


def test_a_reference_listed_twice_in_one_term_counts_once():
    g = graph()
    g["@graph"][7]["object"].append(ref("#pub-j-0"))
    assert Index(g).job_of("#pub-j-0")["@id"] == "#job-j"


def test_files_are_found_by_digest_never_by_name_and_all_of_them():
    idx = Index(graph())
    assert [e["@id"] for e in idx.files_by_sha256("b" * 64)] == ["run/line.json", "run/twin.json"]
    assert [e["@id"] for e in idx.files_by_sha256("a" * 64)] == ["run/raw.json"]
    assert idx.files_by_sha256("c" * 64) == [] and idx.files_by_sha256(None) == [] and idx.files_by_sha256(5) == []
    assert idx.files_by_sha256("b" * 64) is not idx.files_by_sha256("b" * 64)


@pytest.mark.parametrize("pub, k", [("#pub-db1nms2vog1s73fidhc0-0", 0), ("#pub-j-9", 9),
                                    ("#pub-8586f1cc-a312-4ad4-8f4b-2ff2524676ae-0", 0), ("#pub-x-1-1", 1)])
def test_a_pubs_index_is_the_last_segment_of_its_id(pub, k):
    assert Index(graph()).pub_index(pub) == k and Index(graph()).pub_index({"@id": pub}) == k


@pytest.mark.parametrize("pub", ["#pub-j-10", "#pub-j", "#pub-j-a", "#pub-j-", "#pub-j-٠", "pub", "#pub-j-1-",
                                 "#pub-j-1x"])
def test_an_id_that_does_not_end_in_one_decimal_digit_has_no_pub_index(pub):
    with pytest.raises(GraphError, match="its PUB index"):
        Index(graph()).pub_index(pub)


def test_two_entities_of_one_id_or_one_without_an_id_are_refused():
    g = graph()
    g["@graph"].append({"@id": "#device", "@type": "IndividualProduct"})
    with pytest.raises(GraphError, match="an @id twice"):
        Index(g)
    for bad in ({"@type": "File"}, {"@id": 5}, "x", None):
        with pytest.raises(GraphError, match="without an @id"):
            Index({"@graph": [bad]})


@pytest.mark.parametrize("types", [[{"@id": "x"}], [["a"]], ["File", {}], [5], [None]])
def test_a_type_that_is_not_a_string_is_a_graph_error_not_a_crash(types):
    """The reader refuses one at step 1; an Index is also built from a generator's entities, and a step is also handed
    metadata the reader has not seen."""
    with pytest.raises(GraphError, match="a type that is not a string"):
        Index({"@graph": [{"@id": "#a", "@type": types}]})


def test_a_digest_is_found_on_a_file_and_on_no_other_entity():
    """The verifier's note: an entity that is no File may state a sha256 (a mutant that indexed every entity found it)."""
    g = graph()
    g["@graph"] += [{"@id": "#note", "@type": "CreativeWork", "sha256": "a" * 64},
                    {"@id": "#only-a-note", "@type": ["Dataset", "qro:Pub"], "sha256": "d" * 64}]
    idx = Index(g)
    assert [e["@id"] for e in idx.files_by_sha256("a" * 64)] == ["run/raw.json"]
    assert idx.files_by_sha256("d" * 64) == []


class Counting(dict):
    """A File that counts how often its digest is asked for."""
    reads = 0

    def get(self, key, default=None):
        if key == "sha256":
            Counting.reads += 1
        return super().get(key, default)


def test_the_holders_of_a_relation_and_the_files_by_digest_are_found_once_however_often_they_are_asked(monkeypatch):
    """A crate of 65 jobs asks job_of of each of 68 PUBs: the walk of the graph is made once for each relation."""
    from qro import p1_graph
    g = graph()
    g["@graph"] = [Counting(e) if "File" in types_of(e) else e for e in g["@graph"]]
    idx = Index(g)
    walked, real = [], p1_graph.ref_ids
    monkeypatch.setattr(p1_graph, "ref_ids", lambda v: walked.append(1) or real(v))
    assert idx.job_of("#pub-j-0")["@id"] == "#job-j"
    once = len(walked)
    assert once and idx.job_of("#pub-j-1")["@id"] == "#job-j" and len(walked) == once
    assert idx.decode_of("run/raw.json")["@id"] == "#decode-j"
    twice = len(walked)
    assert twice > once and idx.decode_of("run/raw.json") and idx.job_of_raw("run/raw.json") and len(walked) > twice
    thrice = len(walked)
    assert idx.job_of_raw("run/line.json") and len(walked) == thrice
    Counting.reads = 0
    assert [e["@id"] for e in idx.files_by_sha256("b" * 64)] == ["run/line.json", "run/twin.json"]
    first = Counting.reads
    assert first > 0
    assert idx.files_by_sha256("a" * 64) and idx.files_by_sha256("c" * 64) == [] and Counting.reads == first


@pytest.mark.parametrize("md", [None, {}, [], "x", 5, {"@graph": None}, {"@graph": "abc"}, {"@graph": {"a": 1}},
                                {"@graph": 5}, {"@graph": [[1]]}, {"@graph": ["x"]}, {"@graph": [None]}],
                         ids=["None", "empty", "a list", "a string", "a number", "graph None", "graph a string", "graph a dict",
                              "graph a number", "graph a list of lists", "graph a list of strings", "graph a list of None"])
def test_metadata_that_holds_no_graph_of_entities_is_a_graph_error_not_a_crash(md):
    """The verifier's seam_hostile.py (round 2): a None graph was a TypeError and no @graph a KeyError."""
    with pytest.raises(GraphError):
        Index(md)


def test_what_an_index_builds_at_construction_and_what_it_builds_at_the_first_ask():
    """The docstring says the entities by id and by type are built when the Index is, and the lookups of each relation and
    of the digests when first asked: an entity edited between sees the first unchanged, and the second as it was edited."""
    g = graph()
    idx = Index(g)
    by_id = {e["@id"]: e for e in g["@graph"]}
    by_id["#job-j"]["object"] = [ref("#pub-j-0")]                  # edited after construction, before the first ask
    g["@graph"].append({"@id": "#late", "@type": "qro:Pub"})       # added after construction
    by_id["#device"]["@type"] = "qro:Snapshot"                      # retyped after construction
    assert "#late" not in idx.by_id and idx.of_type("qro:Snapshot") == []        # what was built at construction is as it was
    with pytest.raises(GraphError):                                  # the relation is built now, from the entities as they are:
        idx.job_of("#pub-j-1")                                       # no job lists this pub any more
    by_id["#job-j"]["object"] = [ref("#pub-j-0"), ref("#pub-j-1")]
    with pytest.raises(GraphError):                                  # and is not built again
        idx.job_of("#pub-j-1")
    assert Index(g).job_of("#pub-j-1")["@id"] == "#job-j"            # a new Index sees the graph as it is


def test_an_index_reads_nothing_of_the_metadata_but_its_graph_and_changes_none_of_it():
    md = graph()
    before = json.dumps(md, sort_keys=True)
    idx = Index(md)
    idx.job_of("#pub-j-0"), idx.raw_of(idx.by_id["#job-j"]), idx.files_by_sha256("a" * 64)
    assert json.dumps(md, sort_keys=True) == before
    assert Index(copy.deepcopy(md)).by_id.keys() == idx.by_id.keys()


@pytest.mark.parametrize("kind", [5, 1.5, None, True, {"a": 1}], ids=["a number", "a float", "null", "a bool", "an object"])
def test_an_at_type_that_is_neither_a_string_nor_a_list_is_taken_as_no_type_and_is_no_error(kind):
    """The verifier's D4 of round 3: the docstring said a type that is not a string is a GraphError, and only a list holding
    one is. Any other value of `@type` is taken as no type: the entity is in the index by its @id and in no type's lookup."""
    idx = Index({"@graph": [{"@id": "x", "@type": kind}, {"@id": "y", "@type": "a"}]})
    assert sorted(idx.by_id) == ["x", "y"] and [e["@id"] for e in idx.of_type("a")] == ["y"]
    assert types_of(idx.by_id["x"]) == [] and idx.of_type(str(kind)) == []


def test_an_at_type_that_is_an_empty_string_or_an_empty_list_is_a_type_of_that_name_or_none():
    idx = Index({"@graph": [{"@id": "x", "@type": ""}, {"@id": "y", "@type": []}, {"@id": "z", "@type": ["a", "b"]}]})
    assert [e["@id"] for e in idx.of_type("")] == ["x"] and types_of(idx.by_id["y"]) == []
    assert [e["@id"] for e in idx.of_type("b")] == ["z"]


@pytest.mark.parametrize("kind", [[5], [None], [[1]], [{}], ["a", 5], [True]],
                         ids=["a number", "null", "a list", "an object", "a string and a number", "a bool"])
def test_an_at_type_that_is_a_list_holding_a_non_string_is_a_graph_error_at_construction(kind):
    with pytest.raises(GraphError, match="x: a type that is not a string"):
        Index({"@graph": [{"@id": "x", "@type": kind}]})
