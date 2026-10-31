"""The engine's environment, held to the requirements file version by version (P4's design, item 5): the interpreter that
QRO_SHACL_PYTHON names holds the eight pinned wheels and nothing else but pip, it is outside the repository, and the
requirements file is the eight lines the design read from PyPI, each pinned by SHA-256 so that pip refuses any other file.
Nothing here installs anything: the lead installed the environment, on Logan's word, and a test that found a package
missing would fail, never repair."""
import json
import re
import subprocess
import sys

from p4shacl_helpers import REQUIREMENTS, ROOT, engine_python, requirements

# The design's table (P4.md, item 5), READ from PyPI's JSON pages on 2026-10-15; pip re-checked each hash when it installed.
PINNED = [
    ("pyshacl", "0.40.1", "27dd58c8ddfa103303b4a8c40b2c666332ffc912dbcd3137f7adc7b7bc5e6bda"),
    ("rdflib", "7.6.0", "30c0a3ebf4c0e09215f066be7246794b6492e054e782d7ac2a34c9f70a15e0dd"),
    ("owlrl", "7.6.2", "83347bf7f133979e87b2b18695d51d25510b99cec3f6919b5df05d4fbf058ae0"),
    ("pyparsing", "3.3.3", "ece8c00a69cf01b45d0b1dedabb469c90d8caf996d4fda40f147627a122849a4"),
    ("prettytable", "3.18.0", "b3346e0e6f79180833aebaac088ae926340586cf6d7d991b9eb125b65f72313a"),
    ("wcwidth", "0.9.2", "89ca642c5bf0101157a09366be69fad0379db1f700ae39a920e103234573670e"),
    ("packaging", "26.3", "d7193f7c8e4e93f444fde0262bf90af30e16fa0ad0ad44cb553c87339b23cd1c"),
    ("html5rdf", "1.2.1", "1f519121bc366af3e485310dc8041d2e86e5173c1a320fac3dc9d2604069b83e"),
]
LISTING = ("import importlib.metadata as m, json, sys; print(json.dumps({'python': list(sys.version_info[:3]), "
           "'prefix': sys.prefix, 'packages': {d.metadata['Name'].lower(): d.version for d in m.distributions()}}))")


def test_the_requirements_file_is_the_eight_pinned_lines_the_design_read():
    text = REQUIREMENTS.read_text(encoding="ascii")
    lines = text.splitlines()
    assert "\r" not in text and text.endswith("\n") and len(lines) == 8
    assert [(n, v, h) for n, (v, h) in requirements().items()] == PINNED
    for line, (name, version, digest) in zip(lines, PINNED):
        assert line == f"{name}=={version} --hash=sha256:{digest}"
        assert re.fullmatch(r"[0-9a-f]{64}", digest)


def test_the_requirements_file_is_installable_only_with_hashes_so_pip_refuses_any_other_file():
    for line in REQUIREMENTS.read_text(encoding="ascii").splitlines():
        assert "==" in line and "--hash=sha256:" in line and not re.search(r"[<>~!]=|\*", line)


def test_the_engine_interpreter_holds_exactly_the_pinned_wheels_and_pip():
    done = subprocess.run([engine_python(), "-I", "-c", LISTING], capture_output=True, text=True, timeout=120)
    assert done.returncode == 0, done.stderr[-500:]
    facts = json.loads(done.stdout)
    packages = facts["packages"]
    assert {k: v for k, v in packages.items() if k != "pip"} == {n: v for n, v, _ in PINNED}
    assert tuple(facts["python"][:2]) >= (3, 12)


def test_the_engine_interpreter_is_outside_the_repository_and_a_virtual_environment():
    py = engine_python()
    done = subprocess.run([py, "-I", "-c", LISTING], capture_output=True, text=True, timeout=120)
    prefix = json.loads(done.stdout)["prefix"]
    assert not str(py).lower().startswith(str(ROOT).lower()) and not prefix.lower().startswith(str(ROOT).lower())
    assert prefix != sys.base_prefix and prefix.lower() != sys.prefix.lower()


def test_the_runner_reports_the_versions_of_the_engine_it_ran():
    from p4shacl_helpers import run_engine
    _, versions = run_engine([])
    assert versions == {"pyshacl": PINNED[0][1], "rdflib": PINNED[1][1]}
