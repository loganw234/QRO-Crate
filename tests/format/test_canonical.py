"""The canonical writer: one byte string per metadata, its body, its digest (study QRO-0, section 9 and rule 4)."""
import json

import pytest

from qro import canonical, fixture
from qro.refusal import Refused


def metadata(tmp_path):
    crate = fixture.make(tmp_path / "crate")
    return json.loads((crate / canonical.DESCRIPTOR).read_bytes())


def test_the_writer_is_its_own_fixed_point(tmp_path):
    md = metadata(tmp_path)
    data = canonical.write(md)
    assert canonical.write(json.loads(data)) == data
    assert data.endswith(b"\n") and b"\r" not in data and data.decode("ascii")


def test_the_writer_arranges_the_graph_and_every_list(tmp_path):
    md = metadata(tmp_path)
    shuffled = dict(md, **{"@graph": list(reversed(md["@graph"]))})
    shuffled["@graph"][-2]["hasPart"] = list(reversed(shuffled["@graph"][-2]["hasPart"]))
    assert canonical.write(shuffled) == canonical.write(md)


def test_the_writer_refuses_what_the_reader_refuses(tmp_path):
    md = metadata(tmp_path)
    md["@graph"][1]["keywords"] = "fixture"
    with pytest.raises(Refused) as r:
        canonical.write(md)
    assert r.value.name == "field-kind"


@pytest.mark.parametrize("bad", [5, None, ["x"], {"a": 1}], ids=["a number", "null", "a list", "an object"])
def test_the_writer_refuses_an_id_that_is_no_string_as_the_reader_does(tmp_path, bad):
    """P0.5's first verifier, a note: the writer raised a TypeError, sorting the graph, where the reader refuses the
    same metadata by name (P0.7)."""
    md = metadata(tmp_path)
    md["@graph"].append({"@id": bad, "@type": "Thing"})
    with pytest.raises(Refused) as r:
        canonical.write(md)
    assert (r.value.name, r.value.detail) == ("spelling", "an @id is printable ASCII with no space")


GRAPH = "a list of entities, the descriptor and the root among them"
TOP = "it holds @context and @graph, and nothing else"


@pytest.mark.parametrize("plant, refusal", [
    (lambda md: md["@graph"].append({"@type": "File"}), ("graph-form", "an entity without @id or @type")),
    (lambda md: md["@graph"].append("x"), ("graph-form", GRAPH)),
    (lambda md: md["@graph"].append(["x"]), ("graph-form", GRAPH)),
    (lambda md: md.update({"@graph": "x"}), ("graph-form", GRAPH)),
    (lambda md: md.pop("@graph"), ("graph-form", TOP)),
    (lambda md: md.pop("@context"), ("graph-form", TOP)),
    (lambda md: md["@graph"][1]["hasPart"].append({"x": 1}),
     ("spelling", 'not a reference {"@id": ...} and nothing else')),
    (lambda md: md["@graph"][1].update(name=float("nan")),
     ("spelling", "'NaN': a key twice in one object, or a NaN or infinity")),
], ids=["an entity with no @id", "an entity a string", "an entity a list", "a graph a string", "no graph",
        "no context", "a reference with no @id", "a NaN"])
def test_the_writer_refuses_whatever_it_cannot_arrange_or_spell_as_the_reader_does(tmp_path, plant, refusal):
    """P0.7's first verifier, D3, MEASURED: P0.7's writer gave the reader only an arranging TypeError, and raised
    KeyError, ValueError or TypeError on six other shapes the reader refuses by name; a NaN raised ValueError where
    the reader refuses it `spelling`."""
    md = metadata(tmp_path)
    plant(md)
    with pytest.raises(Refused) as r:
        canonical.write(md)
    assert (r.value.name, r.value.detail) == refusal


def test_the_writer_raises_what_no_reader_can_be_given_and_its_own_failures_as_they_were(tmp_path, monkeypatch):
    """What Python's json cannot write at all gives the reader no bytes: a set is raised as json raises it. A failure
    of the writer's own, on metadata the reader accepts, is raised as it was, never taken for a refusal; and a
    MemoryError is the host's (P0.7)."""
    md, accepted = metadata(tmp_path / "a"), metadata(tmp_path / "b")
    md["@graph"][1]["name"] = {1, 2}
    with pytest.raises(TypeError):
        canonical.write(md)

    def fails(_):
        raise KeyError("the writer's own")
    monkeypatch.setattr(canonical, "arrange", fails)
    with pytest.raises(KeyError):
        canonical.write(accepted)

    def short(_):
        raise MemoryError
    monkeypatch.setattr(canonical, "arrange", short)
    refused = dict(accepted, **{"@graph": accepted["@graph"] + [{"@type": "File"}]})
    for md in (accepted, refused):          # the host's, even where the reader would refuse the metadata
        with pytest.raises(MemoryError):
            canonical.write(md)


def test_the_writer_raises_a_memoryerror_of_its_fallback_as_the_hosts(tmp_path, monkeypatch):
    """P0.7's second verifier, note 7: where the writer could not arrange the metadata and json then ran out of memory
    writing it for the reader, the MemoryError was swallowed and the first failure raised in its place."""
    md = metadata(tmp_path)

    def fails(_):
        raise KeyError("the writer's own")

    def short(*args, **kwargs):
        raise MemoryError
    monkeypatch.setattr(canonical, "arrange", fails)
    monkeypatch.setattr(canonical.json, "dumps", short)
    with pytest.raises(MemoryError):
        canonical.write(md)


def test_the_writer_gives_the_reader_its_metadata_in_one_key_order(tmp_path):
    """P0.7's second verifier, note 3: the writer's fallback gives the reader the metadata with its keys sorted, which
    a generator's need not be. Unsorted, an entity with no @id was refused `spelling`, for the order, not `graph-form`,
    for what it is; and every test passed, since each began from a parsed canonical file, its keys sorted already."""
    def flipped(d):
        return {k: d[k] for k in reversed(list(d))}
    md = metadata(tmp_path)
    md = flipped(dict(md, **{"@graph": [flipped(e) for e in md["@graph"]] + [{"@type": "File"}]}))
    assert list(md) != sorted(md), "the keys out of order: the test's control"
    with pytest.raises(Refused) as r:
        canonical.write(md)
    assert (r.value.name, r.value.detail) == ("graph-form", "an entity without @id or @type")


def test_the_body_drops_the_header_and_only_the_header(tmp_path):
    md = metadata(tmp_path)
    a = canonical.body_digest(md)
    md["@graph"][1]["qro:writtenAt"] = "2027-01-01T00:00:00Z"
    md["@graph"][1]["datePublished"] = "2027-01-01"
    assert canonical.body_digest(md) == a, "two writers' headers differ; the crate's identity does not"
    md["@graph"][1]["name"] = "another name"
    assert canonical.body_digest(md) != a, "a body field is the crate's identity"


def test_an_implementation_is_header_wherever_it_stands(tmp_path):
    """qro:implementation names a definition's implementation, whose version is the body's: two writers' differ."""
    md = metadata(tmp_path)
    a = canonical.body_digest(md)
    md["@graph"][1]["qro:implementation"] = ["qro 0.1.0 on Python 3.12.9"]
    assert canonical.body_digest(canonical.arrange(md)) == a
    assert json.loads(canonical.write(md))["@graph"][1]["qro:implementation"] == ["qro 0.1.0 on Python 3.12.9"]


def test_first_difference_names_a_line_and_column():
    assert canonical.first_difference(b"ab\ncd\n", b"ab\ncx\n") == "line 2 column 2"


def test_the_writer_spells_one_type_as_a_string_and_several_as_a_sorted_list(tmp_path):
    """P0's verifier, round 2: the writer's one-type rule was watched by nothing."""
    md = metadata(tmp_path)
    graph = {e["@id"]: e for e in md["@graph"]}
    graph["data/notes.txt"]["@type"] = ["File"]
    graph["data/raw.counts.json"]["@type"] = ["qro:RawResult", "File"]
    arranged = {e["@id"]: e for e in canonical.arrange(md)["@graph"]}
    assert arranged["data/notes.txt"]["@type"] == "File"
    assert arranged["data/raw.counts.json"]["@type"] == ["File", "qro:RawResult"]
    assert canonical.write(md) == canonical.write(metadata(tmp_path / "again"))


def test_arrange_leaves_its_input_as_it_was(tmp_path):
    """Round 3: with `e = dict(e)` gone, the writer reordered the caller's own lists."""
    import copy
    md = metadata(tmp_path)
    md["@graph"][1]["hasPart"] = list(reversed(md["@graph"][1]["hasPart"]))
    before = copy.deepcopy(md)
    canonical.arrange(md)
    assert md == before


def test_arrange_sorts_only_the_lists_of_list_valued_terms(tmp_path):
    """A key no term names is the reader's to refuse; the writer leaves its order alone."""
    md = metadata(tmp_path)
    md["@graph"][1]["x"] = [3, 1, 2]
    md["@graph"][1]["qro:implementation"] = ["b 2", "a 1"]
    root = canonical.arrange(md)["@graph"][1]
    assert root["x"] == [3, 1, 2] and root["qro:implementation"] == ["a 1", "b 2"]


def test_the_writer_refuses_a_bare_string_for_a_list_valued_term(tmp_path):
    """Round 6, 8.1 item 9: the writer arranges only what is a list, and holds the rest to the reader."""
    md = metadata(tmp_path)
    md["@graph"][1]["qro:implementation"] = "x"
    with pytest.raises(Refused) as r:
        canonical.write(md)
    assert r.value.name == "spelling"
