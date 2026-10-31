"""The engine stage's helpers: a request to the runner (tests/p4shacl/p4shacl_engine.py), as a process of the engine's
own interpreter, and its answers by job id. Nothing here is a test: pytest's naming decides what is one, and a helper
under tests/ names no function `test*` and no class `Test*` (CLAUDE.md).

The interpreter is QRO_SHACL_PYTHON's. Without it this stage is skipped by name at the runner (verify/run.sh); run
by pytest alone, a test here FAILS with the reason, because a test that skips inside a stage fails the stage."""
import json
import os
import subprocess
from pathlib import Path

from qro import vocabulary as V
from qro.p4_expand import BASE
from qro.p4_model import BNode

ROOT = Path(__file__).resolve().parents[2]
RUNNER = ROOT / "tests" / "p4shacl" / "p4shacl_engine.py"
REQUIREMENTS = ROOT / "tests" / "p4shacl" / "p4shacl_requirements.txt"


def engine_python():
    py = os.environ.get("QRO_SHACL_PYTHON")
    assert py and Path(py).is_file(), "QRO_SHACL_PYTHON names no interpreter: the engine stage needs the SHACL engine"
    return py


def run_engine(jobs, timeout=900):
    """The runner's answers to `jobs`, by job id. The interpreter runs isolated (-I), with the network blocked in the
    process by the runner itself."""
    request = {"context": {"path": str(ROOT / "qro" / V.ROCRATE_CONTEXT_FILE), "sha256": V.ROCRATE_CONTEXT_SHA256},
               "base": BASE, "jobs": jobs}
    done = subprocess.run([engine_python(), "-I", str(RUNNER)], input=json.dumps(request), capture_output=True,
                          text=True, encoding="utf-8", timeout=timeout)
    assert done.returncode == 0, f"the runner exited {done.returncode}: {done.stderr[-1500:]}"
    answer = json.loads(done.stdout)
    assert len(answer["results"]) == len(jobs), "the runner answered another number of jobs than it was given"
    return {r["id"]: r for r in answer["results"]}, answer["engine"]


def requirements():
    """The pinned lines of the requirements file: {name: (version, sha256)}."""
    out = {}
    for line in REQUIREMENTS.read_text(encoding="ascii").splitlines():
        if line.strip() and not line.startswith("#"):
            spec, _, digest = line.partition(" --hash=sha256:")
            name, _, version = spec.partition("==")
            out[name] = (version, digest)
    return out


def quick_stage_module(name):
    """A module of the quick stage's tests/p4/, loaded by its path under a name of its own: not imported by name, since
    that stage's directory is on no path here, and not through `tests.`, which a package in site-packages shadows. The
    directory is put on the path for the helpers that import their sibling helpers by name (p4_sweeps, p4_helpers), as
    pytest's rootdir mode does for them in their own stage."""
    import importlib.util
    import sys
    if str(ROOT / "tests" / "p4") not in sys.path:
        sys.path.insert(0, str(ROOT / "tests" / "p4"))
    spec = importlib.util.spec_from_file_location(f"{name}_of_the_quick_stage", ROOT / "tests" / "p4" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def shape_files():
    """The shapes the engine reads: the committed Turtle files of profile/validator/qro-crate/, must/ then should/."""
    base = ROOT / "profile" / "validator" / "qro-crate"
    return [str(p).replace("\\", "/") for folder in ("must", "should") for p in sorted((base / folder).glob("*.ttl"))]


def term(t):
    """A term of p4_model as the runner names one: ["iri", v], ["bnode"], ["lit", lexical, datatype]."""
    if isinstance(t, str):
        return ("iri", t)
    if isinstance(t, BNode):
        return ("bnode",)
    return ("lit", t.lexical, t.datatype)


def engine_term(j):
    return ("bnode",) if j[0] == "bnode" else tuple(j)


def mine(triples):
    """The expansion's triples, as a set of the runner's terms."""
    return {(term(s), p, term(o)) for s, p, o in triples}


def theirs(triples):
    """The runner's triples (rdflib's), as a set of the same terms."""
    return {(engine_term(s), p, engine_term(o)) for s, p, o in triples}


def failing_must(answer):
    """The local names of the must shapes a real engine's report fails (severity Violation), sorted."""
    return sorted({r["shape"].split("#", 1)[1] for r in answer["results"] if r["severity"] == "Violation"})


def unclaimed(cases, claims):
    """[name] for each case (name, the checker's refusal, the must shapes the engine fails) on which the engine fails a must
    shape and none of the failing shapes claims the refusal: a claim that does not hold (`claims` is {shape: its claims})."""
    return sorted(name for name, refusal, failing in cases
                  if failing and refusal not in {c for f in failing for c in claims[f]})


def without(claims, shapes, refusal):
    """`claims` with `refusal` taken away from the shapes named: the claim, watched failing."""
    return {s: tuple(c for c in cs if c != refusal) if s in shapes else cs for s, cs in claims.items()}
