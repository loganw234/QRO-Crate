"""The seam with P2 (P1's design, item 8; the lead's decision 3 on it): P1's generators call qro.p2_measures if it is
present, by name, and never otherwise; the adapter asks it for the files of the question first. Tested here with a
stand-in module, since P2's is built beside this one and the lead's merge runs the two together. The stand-in is put in
sys.modules, where the generator finds a parcel's module as the checker does, so the real lookup is the one tested.

None of these builds is checked by the whole checker: a stand-in's terms are not P2's, and P2's own steps, which enter
on its terms, would be right to refuse them.

One tree each (the lead's ruling, 2026-11-08): these tests mean P1 alone with a module they put in place, so the twin
they take is the one built with P2's module absent (`Sandbox(alone=True)`), and the module in sys.modules is the
stand-in for the generator and the adapter both. Where P1 calls `contribute` only for a crate that holds files under
question/, a test that wants it called gives the crate one. The tree as merged, with P2's own module, is
tests/p1/test_p1_merged.py's."""
import importlib.util
import os
import subprocess
import sys
from pathlib import Path

import pytest

from controls import plants_p1 as plants
from p1_support import (MORNING_COH, MORNING_KA, ROOT, TWIN, Sandbox, generated, graph, guard, memo_parses, of_type,
                        standin, synthetic_atlas)
from qro import canonical, p1_adapter, p1_decode, p1_generate as G, reader
from qro import vocabulary as V

KA_LINE, COH_LINE = f"{MORNING_KA}-line.json", f"{MORNING_COH}-line.json"
NAME = "qro.p2_measures"


@pytest.fixture(scope="module")
def working(tmp_path_factory):
    """The one hard-linked working copy of the twin these tests share, and the proof at the end that none was written
    through."""
    box = Sandbox(tmp_path_factory.mktemp("sandbox"), alone=True)
    yield box
    box.verify_pristine()


@pytest.fixture
def crate(working, monkeypatch):
    """The working copy, as the twin is, with the snapshots parsed once in the process; restored after the test."""
    memo_parses(monkeypatch)
    yield working.root
    working.restore()


@pytest.fixture
def served(crate):
    """The working copy with a file under question/, written through no link: the crate P2 has a law for, whose metadata
    P1 asks P2's `contribute` for."""
    plants.write_file(crate, "question/law.json", b"{}\n")
    return crate


def installed(monkeypatch, module):
    monkeypatch.setitem(sys.modules, NAME, module)
    return module


def absent(monkeypatch):
    monkeypatch.delitem(sys.modules, NAME, raising=False)
    real = importlib.util.find_spec
    monkeypatch.setattr(importlib.util, "find_spec", lambda name, *a: None if name == NAME else real(name, *a))


def test_the_module_is_found_by_name_where_a_parcels_module_is(monkeypatch):
    module = installed(monkeypatch, standin())
    assert G.p2_module() is module


def test_with_no_module_there_is_no_seam_and_the_question_holds_only_p1s_terms(crate, monkeypatch):
    absent(monkeypatch)
    assert G.p2_module() is None
    md = generated(crate)
    assert set(graph(md)["#question"]) == {"@id", "@type", "name", "description", "object"}
    assert "#question-files" not in graph(md)


@pytest.mark.parametrize("without", ["question_files", "contribute"])
def test_a_module_present_without_one_of_its_functions_is_a_seam_raise(crate, monkeypatch, without):
    module = standin()
    delattr(module, without)
    installed(monkeypatch, module)
    g = guard(crate)
    assert (g.guard, g.where) == ("seam", NAME) and without in g.detail


@pytest.mark.parametrize("value", [None, "contribute", 3, [lambda: 0]])
def test_a_function_that_is_not_callable_is_not_a_function(crate, monkeypatch, value):
    module = standin()
    module.contribute = value
    installed(monkeypatch, module)
    assert guard(crate).guard == "seam"


def test_contribute_is_called_once_with_the_crate_and_a_copy_of_the_entities_by_id(crate, served, monkeypatch):
    calls = []

    def contribute(crate_dir, entities):
        calls.append((crate_dir, entities))
        entities["#question"]["name"] = "changed by P2"
        entities[next(i for i in entities if i.startswith("#job-"))]["name"] = "changed by P2"
        return {}, []
    installed(monkeypatch, standin(contribute=contribute))
    md = generated(crate)
    (crate_dir, entities), = calls
    assert isinstance(crate_dir, Path) and crate_dir == crate and type(entities) is dict
    assert all(k == e["@id"] for k, e in entities.items())
    assert {"./", canonical.DESCRIPTOR, V.PROFILE, V.PROCESS_RUN_CRATE}.isdisjoint(entities)
    assert "#question" in entities and sum(i.startswith("#pub-") for i in entities) == 5
    assert len([i for i, e in entities.items() if "File" in canonical.types(e)]) == 73          # 72 records and question/law.json
    assert all("sha256" in e for e in entities.values() if "File" in canonical.types(e))
    assert graph(md)["#question"]["name"] == "The question"                    # it was handed a copy
    assert not any(e.get("name") == "changed by P2" for e in md["@graph"])


def test_the_generator_never_asks_for_the_files_of_the_question_the_adapter_does(crate, monkeypatch):
    def boom(crate_dir):
        raise AssertionError("the generator asked for the question's files")
    installed(monkeypatch, standin(question_files=boom))
    generated(crate)


def test_p2s_terms_and_entities_join_p1s_and_the_root_mentions_every_action(crate, served, monkeypatch):
    measuring = {"@id": "#measuring", "@type": ["CreateAction", "qro:Measuring"], "name": "the measuring",
                 "qro:alpha": "1/20", "qro:family": 3}
    installed(monkeypatch, standin(contribute=lambda c, e: ({"qro:measureSet": "qro-measures/1"}, [measuring])))
    md = generated(crate)
    ids = graph(md)
    assert ids["#question"]["qro:measureSet"] == "qro-measures/1" and ids["#measuring"] == measuring
    root = md["@graph"][1]
    assert "#measuring" in {r["@id"] for r in root["mentions"]} and len(root["mentions"]) == 12
    assert "#measuring" not in {r["@id"] for r in root["hasPart"]}
    assert canonical.write(md)                      # the strict reader holds the merged metadata


def test_new_entities_may_be_a_dict_by_id(crate, served, monkeypatch):
    e = {"@id": "#hold-x", "@type": ["CreateAction", "qro:Hold"], "qro:holdRule": "qro-exact-hold/1"}
    installed(monkeypatch, standin(contribute=lambda c, ents: ({}, {"#hold-x": e})))
    assert graph(generated(crate))["#hold-x"] == e


@pytest.mark.parametrize("term", ["@id", "@type", "name", "description", "object"])
def test_a_term_p1_writes_on_the_question_is_a_seam_raise(crate, served, monkeypatch, term):
    installed(monkeypatch, standin(contribute=lambda c, e: ({term: "x"}, [])))
    g = guard(crate)
    assert g.guard == "seam" and term in g.detail


@pytest.mark.parametrize("terms", [[], "terms", None, 3])
def test_question_terms_that_are_no_dict_are_a_seam_raise(crate, served, monkeypatch, terms):
    installed(monkeypatch, standin(contribute=lambda c, e: (terms, [])))
    g = guard(crate)
    assert g.guard == "seam" and "no dict" in g.detail


@pytest.mark.parametrize("new", [
    [{"@id": "#question", "@type": "CreativeWork"}],
    [{"@id": "#x", "@type": "CreativeWork"}, {"@id": "#x", "@type": "CreativeWork"}],
    ["not an entity"], [3], [{"@type": "CreativeWork"}], [{"@id": 7, "@type": "CreativeWork"}],
], ids=["P1's id", "one id twice", "a string", "a number", "no @id", "an @id that is no string"])
def test_an_entity_that_is_no_entity_or_holds_an_id_already_held_is_a_seam_raise(crate, served, monkeypatch, new):
    installed(monkeypatch, standin(contribute=lambda c, e: ({}, new)))
    g = guard(crate)
    assert g is not None and g.guard == "seam"


def test_an_id_p1_holds_is_a_seam_raise_whatever_the_entity(crate, served, monkeypatch):
    installed(monkeypatch, standin())
    job = next(e["@id"] for e in of_type(generated(crate), "qro:Job"))
    installed(monkeypatch, standin(contribute=lambda c, e: ({}, [{"@id": job, "@type": "CreativeWork"}])))
    assert guard(crate).guard == "seam"


# -- what P2 raises (the lead's ruling, 2026-11-08): the records refused by the seam, the host's failures the host's --------------------------------
def raising(error):
    def fails(*args):
        raise error
    return fails


@pytest.mark.parametrize("error", [RuntimeError("P2 cannot read this crate"), ValueError("no law"), KeyError("k"),
                                   AssertionError("p2 asserted"), Exception("a base exception")],
                         ids=["RuntimeError", "ValueError", "KeyError", "AssertionError", "Exception"])
def test_a_contribute_that_raises_is_the_records_refused_by_the_seam(crate, served, monkeypatch, error):
    installed(monkeypatch, standin(contribute=raising(error)))
    g = guard(crate)
    assert (g.guard, g.where) == ("seam", NAME)
    assert g.detail.startswith(f"contribute raised {type(error).__name__}: ") and str(error) in g.detail


@pytest.mark.parametrize("error", [OSError("the disk"), PermissionError("denied"), MemoryError("no memory")],
                         ids=["OSError", "PermissionError", "MemoryError"])
def test_a_contribute_that_raises_the_hosts_failure_raises_it_out_of_the_generator_as_it_is(crate, served, monkeypatch,
                                                                                            error):
    installed(monkeypatch, standin(contribute=raising(error)))
    with pytest.raises(type(error)):
        generated(crate)


def test_a_crate_that_holds_no_file_under_question_never_has_contribute_called(crate, monkeypatch):
    """A crate P2 has no law for carries none of P2's terms: `question_files` wrote none, so there is nothing under
    question/, and `contribute`, which raises for such a crate in P2's own module, is not called."""
    def boom(crate_dir, entities):
        raise AssertionError("the generator called contribute for a crate with no file under question/")
    installed(monkeypatch, standin(contribute=boom))
    md = generated(crate)
    assert set(graph(md)["#question"]) == {"@id", "@type", "name", "description", "object"}
    assert "#question-files" not in graph(md)


def test_contribute_can_read_every_pubs_counts_through_the_entities_alone(crate, served, monkeypatch):
    """What P2 does while the metadata is being made: `pub_counts` on {"@graph": entities}, when no metadata file exists."""
    seen = {}

    def contribute(crate_dir, entities):
        graph_ = {"@graph": list(entities.values())}
        for i in sorted(e for e in entities if e.startswith("#pub-")):
            seen[i] = sum(p1_decode.pub_counts(crate_dir, graph_, i).values())
        return {}, []
    installed(monkeypatch, standin(contribute=contribute))
    generated(crate)
    assert sorted(seen.values()) == [1024, 1024, 1024, 4096, 4096]


# -- the files of the question ---------------------------------------------------------------------------------------------------------
def test_files_under_question_fit_the_layout_while_the_module_is_present(crate, monkeypatch):
    installed(monkeypatch, standin())
    plants.write_file(crate, "question/law.json", b"{}\n")
    plants.write_file(crate, "question/deeper/x.txt", b"x")
    md = generated(crate)
    ids = graph(md)
    assert ids["question/law.json"]["license"] == {"@id": "https://creativecommons.org/licenses/by/4.0/"}
    assert ids["question/deeper/x.txt"]["encodingFormat"] == "text/plain" and ids["question/law.json"]["contentSize"] == "3"
    assert [r["@id"] for r in ids["#question-files"]["hasPart"]] == ["question/deeper/x.txt", "question/law.json"]
    assert "#question-files" in {r["@id"] for r in md["@graph"][1]["hasPart"]}


def test_a_question_directory_with_no_file_makes_no_dataset(crate, monkeypatch):
    installed(monkeypatch, standin())
    (crate / "question").mkdir()
    assert "#question-files" not in graph(generated(crate))


# -- the adapter: the files of the question are asked for after the records are copied, and before the metadata -----------------------------
def build(tmp_path, monkeypatch, **kw):
    memo_parses(monkeypatch)
    return p1_adapter.build("ibm", TWIN, tmp_path / "out", sliced=True, **kw)


def test_the_adapter_writes_the_files_p2_names_before_it_generates(tmp_path, monkeypatch):
    seen = {}

    def question_files(crate_dir):
        seen["records_copied"] = (crate_dir / "2026-09-25" / "p3" / "circuit-ed767c01bd4b851d.qasm").is_file()
        seen["no_metadata_yet"] = not (crate_dir / canonical.DESCRIPTOR).exists()
        return {"law.json": b"{}\n", "sub/notes.txt": b"x"}
    installed(monkeypatch, standin(question_files=question_files,
                                   contribute=lambda c, e: ({"qro:law": {"@id": "question/law.json"}}, [])))
    done = build(tmp_path, monkeypatch)
    out = tmp_path / "out"
    assert seen == {"records_copied": True, "no_metadata_yet": True}
    assert (out / "question" / "law.json").read_bytes() == b"{}\n" and (out / "question" / "sub" / "notes.txt").is_file()
    md = reader.read((out / canonical.DESCRIPTOR).read_bytes())
    assert graph(md)["#question"]["qro:law"] == {"@id": "question/law.json"} and done["files"] == 75


def test_without_the_module_the_adapter_writes_no_question_directory(tmp_path, monkeypatch):
    absent(monkeypatch)
    build(tmp_path, monkeypatch)
    assert not (tmp_path / "out" / "question").exists()


@pytest.mark.parametrize("key", ["", "/abs", "../up", "a/../b", "back\\slash", "a b", "C:x", "dot.", 1, None, b"law.json"])
def test_a_name_that_is_not_a_path_under_question_is_a_seam_raise_and_leaves_nothing(tmp_path, monkeypatch, key):
    installed(monkeypatch, standin(question_files=lambda c: {key: b"x"}))
    with pytest.raises(G.GuardError) as x:
        build(tmp_path, monkeypatch)
    assert x.value.guard == "seam" and not (tmp_path / "out").exists()


def test_a_file_that_is_not_bytes_is_a_seam_raise(tmp_path, monkeypatch):
    installed(monkeypatch, standin(question_files=lambda c: {"law.json": "text"}))
    with pytest.raises(G.GuardError) as x:
        build(tmp_path, monkeypatch)
    assert x.value.guard == "seam"


def test_two_names_that_differ_only_by_case_are_a_seam_raise(tmp_path, monkeypatch):
    installed(monkeypatch, standin(question_files=lambda c: {"Law.json": b"{}\n", "law.json": b"{}\n"}))
    with pytest.raises(G.GuardError) as x:
        build(tmp_path, monkeypatch)
    assert x.value.guard == "seam" and "case" in x.value.detail and not (tmp_path / "out").exists()


def test_a_question_files_that_names_none_is_a_crate_p2_has_no_law_for_and_contribute_is_never_called(tmp_path,
                                                                                                      monkeypatch):
    def boom(crate_dir, entities):
        raise AssertionError("the adapter's generator called contribute for a crate whose question_files named none")
    installed(monkeypatch, standin(question_files=lambda c: {}, contribute=boom))
    done = build(tmp_path, monkeypatch)
    out = tmp_path / "out"
    assert not (out / "question").exists() and done["files"] == 73
    md = reader.read((out / canonical.DESCRIPTOR).read_bytes())
    assert set(graph(md)["#question"]) == {"@id", "@type", "name", "description", "object"}


@pytest.mark.parametrize("function", ["question_files", "contribute"])
@pytest.mark.parametrize("error", [ValueError("P2 has no law for this crate"), KeyError("law"), RuntimeError("r"),
                                   Exception("e")], ids=["ValueError", "KeyError", "RuntimeError", "Exception"])
def test_a_raise_of_p2_in_a_build_is_the_records_refused_by_the_seam_and_leaves_nothing(tmp_path, monkeypatch, function,
                                                                                         error):
    served = {"question_files": lambda c: {"law.json": b"{}\n"}}
    installed(monkeypatch, standin(**{**served, function: raising(error)}))
    with pytest.raises(G.GuardError) as x:
        build(tmp_path, monkeypatch)
    assert (x.value.guard, x.value.where) == ("seam", NAME)
    assert x.value.detail == f"{function} raised {type(error).__name__}: {error}" and not (tmp_path / "out").exists()


@pytest.mark.parametrize("function", ["question_files", "contribute"])
@pytest.mark.parametrize("error", [OSError("the disk"), MemoryError("no memory")], ids=["OSError", "MemoryError"])
def test_the_hosts_failure_in_p2_in_a_build_is_raised_as_it_is_and_leaves_nothing(tmp_path, monkeypatch, function, error):
    served = {"question_files": lambda c: {"law.json": b"{}\n"}}
    installed(monkeypatch, standin(**{**served, function: raising(error)}))
    with pytest.raises(type(error)):
        build(tmp_path, monkeypatch)
    assert not (tmp_path / "out").exists()


@pytest.mark.parametrize("answer", [None, [], [("law.json", b"x")], "law.json", 3],
                         ids=["None", "a list", "a list of pairs", "a string", "a number"])
def test_a_question_files_answer_that_is_no_dict_is_a_seam_raise(tmp_path, monkeypatch, answer):
    installed(monkeypatch, standin(question_files=lambda c: answer))
    with pytest.raises(G.GuardError) as x:
        build(tmp_path, monkeypatch)
    assert x.value.guard == "seam" and "no dict" in x.value.detail and not (tmp_path / "out").exists()


@pytest.mark.parametrize("answer", [None, {}, ({}, [], 3), ({},), "ab", ({}, "text"), ({}, 3)],
                         ids=["None", "a dict", "a triple", "a single", "a string", "terms and a string",
                              "terms and a number"])
def test_a_contribute_answer_that_is_not_terms_and_entities_is_a_seam_raise(crate, served, monkeypatch, answer):
    installed(monkeypatch, standin(contribute=lambda c, e: answer))
    g = guard(crate)
    assert g is not None and g.guard == "seam"


# -- the adapter as a process, P2's module a stand-in that raises (tests/p1/p1_standin.py) --------------------------------------------------
STANDIN = Path(__file__).resolve().with_name("p1_standin.py")


def standin_process(tmp_path, function, raised):
    env = {k: v for k, v in os.environ.items() if k != "PYTHONSAFEPATH"}
    env.update(PYTHONIOENCODING="utf-8", PYTHONPATH=str(ROOT))
    return subprocess.run([sys.executable, str(STANDIN), function, raised, "--", "ibm", "--moth", str(TWIN), "--out",
                           str(tmp_path / "out"), "--slice"], capture_output=True, env=env, cwd=ROOT)


@pytest.mark.parametrize("function", ["question_files", "contribute"])
def test_the_process_calls_a_raise_of_p2_the_records_refused_and_never_the_adapter_failing(tmp_path, function):
    p = standin_process(tmp_path, function, "value")
    line = p.stdout.decode("ascii")
    assert (p.returncode, p.stderr) == (1, b"") and line.count("\n") == 1, (p.stdout[-300:], p.stderr[-300:])
    assert line == (f"REFUSED metadata-generated at {NAME}: seam: {function} raised ValueError: P2 has no law for this "
                    "crate \\xe9\n")
    assert not (tmp_path / "out").exists()


@pytest.mark.parametrize("function", ["question_files", "contribute"])
@pytest.mark.parametrize("raised", ["os", "memory"])
def test_the_process_calls_the_hosts_failure_in_p2_the_adapter_failing_and_leaves_nothing(tmp_path, function, raised):
    p = standin_process(tmp_path, function, raised)
    assert (p.returncode, p.stdout) == (3, b"") and p.stderr.startswith(b"FAILED: the adapter itself failed, ")
    assert not (tmp_path / "out").exists()


def test_the_process_with_a_stand_in_that_raises_nowhere_builds(tmp_path):
    p = standin_process(tmp_path, "contribute", "none")
    assert (p.returncode, p.stderr) == (0, b"") and p.stdout.startswith(b"BUILT ibm: 74 files, "), p.stdout[-300:]
    assert (tmp_path / "out" / "question" / "law.json").is_file()


# -- the Atlas path: the same seam, on a crate made here (no Moth byte is committed) ------------------------------------------------------
@pytest.fixture
def atlas(tmp_path):
    return synthetic_atlas(tmp_path)


@pytest.fixture
def served_atlas(atlas):
    """The Atlas crate with a file under question/: the crate P2 has a law for."""
    plants.write_file(atlas, "question/law.json", b"{}\n")
    return atlas


def test_with_no_module_the_atlas_question_holds_only_p1s_terms(atlas, monkeypatch):
    absent(monkeypatch)
    assert G.p2_module() is None
    md = generated(atlas, "atlas")
    assert set(graph(md)["#question"]) == {"@id", "@type", "name", "description", "object"}
    assert "#question-files" not in graph(md)


@pytest.mark.parametrize("without", ["question_files", "contribute"])
def test_a_module_present_without_one_of_its_functions_is_a_seam_raise_on_the_atlas_path_too(atlas, monkeypatch, without):
    module = standin()
    delattr(module, without)
    installed(monkeypatch, module)
    g = guard(atlas, "atlas")
    assert (g.guard, g.where) == ("seam", NAME) and without in g.detail


def test_contribute_is_called_once_with_the_atlas_crate_and_a_copy_of_its_entities_by_id(atlas, served_atlas,
                                                                                           monkeypatch):
    calls = []

    def contribute(crate_dir, entities):
        calls.append((crate_dir, entities))
        entities["#question"]["name"] = "changed by P2"
        return {}, []
    installed(monkeypatch, standin(contribute=contribute))
    md = generated(atlas, "atlas")
    (crate_dir, entities), = calls
    assert isinstance(crate_dir, Path) and crate_dir == atlas and type(entities) is dict
    assert all(k == e["@id"] for k, e in entities.items())
    assert {"./", canonical.DESCRIPTOR, V.PROFILE, V.PROCESS_RUN_CRATE}.isdisjoint(entities)
    pubs = [e for e in entities.values() if "qro:Pub" in canonical.types(e)]
    assert len(pubs) == 3 and all(p["qro:commitment"] == "none" and "qro:basis" not in p for p in pubs)
    assert sum(i.startswith("#job-") for i in entities) == 3 and sum(i.startswith("#decode-") for i in entities) == 3
    assert not [e for e in entities.values() if "qro:Compile" in canonical.types(e)]          # Atlas runs no compile
    assert all("sha256" in e for e in entities.values() if "File" in canonical.types(e))
    assert graph(md)["#question"]["name"] == "The question"                                   # it was handed a copy


def test_p2s_terms_and_entities_join_the_atlas_graph_and_the_root_mentions_every_action(atlas, served_atlas,
                                                                                         monkeypatch):
    measuring = {"@id": "#measuring", "@type": ["CreateAction", "qro:Measuring"], "name": "the measuring",
                 "qro:alpha": "1/20", "qro:family": 3}
    installed(monkeypatch, standin(contribute=lambda c, e: ({"qro:measureSet": "qro-measures/1"}, [measuring])))
    md = generated(atlas, "atlas")
    ids = graph(md)
    assert ids["#question"]["qro:measureSet"] == "qro-measures/1" and ids["#measuring"] == measuring
    root = md["@graph"][1]
    assert "#measuring" in {r["@id"] for r in root["mentions"]} and len(root["mentions"]) == 3 + 3 + 1
    assert "#measuring" not in {r["@id"] for r in root["hasPart"]}
    assert canonical.write(md)


def test_an_id_p1_holds_on_the_atlas_path_is_a_seam_raise_whatever_the_entity(atlas, served_atlas, monkeypatch):
    installed(monkeypatch, standin())
    job = next(e["@id"] for e in of_type(generated(atlas, "atlas"), "qro:Job"))
    installed(monkeypatch, standin(contribute=lambda c, e: ({}, [{"@id": job, "@type": "CreativeWork"}])))
    assert guard(atlas, "atlas").guard == "seam"


def test_a_crate_that_holds_no_file_under_question_never_has_contribute_called_on_the_atlas_path_either(atlas,
                                                                                                         monkeypatch):
    def boom(crate_dir, entities):
        raise AssertionError("the generator called contribute for an Atlas crate with no file under question/")
    installed(monkeypatch, standin(contribute=boom))
    md = generated(atlas, "atlas")
    assert set(graph(md)["#question"]) == {"@id", "@type", "name", "description", "object"}


@pytest.mark.parametrize("error", [ValueError("no law"), OSError("disk")], ids=["ValueError", "OSError"])
def test_a_raise_of_contribute_on_the_atlas_path_is_the_seams_or_the_hosts(atlas, served_atlas, monkeypatch, error):
    installed(monkeypatch, standin(contribute=raising(error)))
    if isinstance(error, OSError):
        with pytest.raises(OSError):
            generated(atlas, "atlas")
    else:
        g = guard(atlas, "atlas")
        assert (g.guard, g.where) == ("seam", NAME) and g.detail == f"contribute raised ValueError: {error}"


def test_files_under_question_fit_the_atlas_layout_only_while_the_module_is_present(atlas, monkeypatch):
    plants.write_file(atlas, "question/law.json", b"{}\n")
    absent(monkeypatch)
    g = guard(atlas, "atlas")
    assert (g.guard, g.where) == ("G12", "question/law.json")
    installed(monkeypatch, standin())
    ids = graph(generated(atlas, "atlas"))
    assert [r["@id"] for r in ids["#question-files"]["hasPart"]] == ["question/law.json"]
    assert ids["question/law.json"]["license"] == {"@id": "https://creativecommons.org/licenses/by/4.0/"}
