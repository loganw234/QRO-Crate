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
