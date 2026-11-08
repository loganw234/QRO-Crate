"""P1 and P2 together, the tree as merged (the lead's ruling, 2026-11-08): nothing here pins or replaces P2's module, so the
adapter, the generator and the checker all see qro.p2_measures as the tree holds it. One tree each: no test builds with one
and generates with the other. The adapter is run as a process, as a user runs it.

  - a crate P2 has a law for (the twin: it holds the source circuit) is built with question/law.json and P2's terms and
    entities, is accepted by the whole checker, steps 6 and 7 among its steps, and regenerates as built;
  - a crate P2 has no law for (a synthetic Atlas slice: its circuit is no circuit P2 knows) is built, exit 0, with no file
    under question/ and none of P2's terms, is accepted by the whole checker, and regenerates as built."""
import importlib.util
import os
import re
import subprocess
import sys

import pytest

from p1_support import ROOT, TWIN, generated, graph, types_of
from qro import canonical, checker, p1_generate as G, reader

P2_TERMS = ("qro:law", "qro:lawCircuit", "qro:measureSet", "qro:twins")
BUILT = re.compile(r"BUILT (ibm|atlas): ([0-9]+) files, ([0-9]+) bytes, identity ([0-9a-f]{64})\n")


def adapter(argv):
    env = {k: v for k, v in os.environ.items() if k != "PYTHONSAFEPATH"}
    env.update(PYTHONIOENCODING="utf-8", PYTHONPATH=str(ROOT))
    return subprocess.run([sys.executable, "-m", "qro.p1_adapter", *argv], capture_output=True, env=env, cwd=ROOT)


@pytest.fixture(scope="module")
def twin(tmp_path_factory):
    out = tmp_path_factory.mktemp("merged-twin") / "crate"
    p = adapter(["ibm", "--moth", str(TWIN), "--out", str(out), "--slice"])
    assert (p.returncode, p.stderr) == (0, b""), (p.stdout[-300:], p.stderr[-300:])
    return out, BUILT.fullmatch(p.stdout.decode("ascii"))


@pytest.fixture(scope="module")
def slice_with_no_law(tmp_path_factory):
    """A synthetic Atlas slice, laid out as moth-quantum's: P2 knows no law for its circuit."""
    from test_p1_adapter import synthetic_moth
    tmp = tmp_path_factory.mktemp("merged-atlas")
    _, moth = synthetic_moth(tmp)
    out = tmp / "out"
    p = adapter(["atlas", "--moth", str(moth), "--out", str(out), "--slice"])
    assert (p.returncode, p.stderr) == (0, b""), (p.stdout[-300:], p.stderr[-300:])
    return out, BUILT.fullmatch(p.stdout.decode("ascii"))


def test_the_tree_holds_p2s_module_and_the_generator_finds_it():
    assert importlib.util.find_spec("qro.p2_measures") is not None
    assert G.p2_module().__name__ == "qro.p2_measures"


def test_a_crate_p2_has_a_law_for_is_built_with_the_law_and_p2s_terms(twin):
    out, line = twin
    assert (out / "question" / "law.json").is_file() and line is not None
    ids = graph(reader.read((out / canonical.DESCRIPTOR).read_bytes()))
    assert all(t in ids["#question"] for t in P2_TERMS) and ids["#question"]["qro:law"] == {"@id": "question/law.json"}
    assert "#measuring" in ids and "#question-files" in ids
    assert int(line.group(2)) == sum(1 for p in out.rglob("*") if p.is_file())


def test_a_crate_p2_has_a_law_for_is_accepted_by_the_whole_checker_and_regenerates_as_built(twin):
    out, line = twin
    checker.load()
    assert canonical.body_digest(checker.check(out)) == line.group(4) == canonical.body_digest(generated(out))


def test_a_slice_with_no_source_circuit_is_built_with_no_question_file_and_none_of_p2s_terms(slice_with_no_law):
    out, line = slice_with_no_law
    assert line is not None and line.group(1) == "atlas" and not (out / "question").exists()
    md = reader.read((out / canonical.DESCRIPTOR).read_bytes())
    ids = graph(md)
    assert not any(t in ids["#question"] for t in P2_TERMS)
    assert not [e for e in md["@graph"] if {"qro:Measuring", "qro:Measurement", "qro:Contrast", "qro:Hold"} & set(types_of(e))]
    assert "#question-files" not in ids


def test_a_slice_with_no_source_circuit_is_accepted_by_the_whole_checker_and_regenerates_as_built(slice_with_no_law):
    """Steps 6 and 7 accept a crate that carries none of their terms, and step 9's generator gives the same answer."""
    out, line = slice_with_no_law
    checker.load()
    assert canonical.body_digest(checker.check(out)) == line.group(4) == canonical.body_digest(generated(out, "atlas"))
