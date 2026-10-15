"""The tools' own checks, each watched to fail (HonestFramework, METHOD.md section 3; P0's verifier's notes): the
vocabulary's --check on a changed or missing file, the instruments' check on a wrong checkout, and the privacy
gate's alternatives walked both ways against their plants."""
import importlib.util
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


def load(rel):
    spec = importlib.util.spec_from_file_location(Path(rel).stem, ROOT / rel)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


gen = load("tools/gen_vocabulary.py")
privacy = load("tools/check_privacy.py")


def copy_outputs(tmp_path):
    for rel in gen.OUTPUTS:
        (tmp_path / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / rel, tmp_path / rel)
    return tmp_path


def test_the_generated_files_are_what_their_definitions_render():
    assert gen.problems() == []
    assert gen.drift(ROOT) == []


@pytest.mark.parametrize("rel", sorted(gen.OUTPUTS))
def test_a_changed_byte_in_a_generated_file_is_drift(tmp_path, rel):
    root = copy_outputs(tmp_path)
    data = bytearray((root / rel).read_bytes())
    data[len(data) // 2] ^= 1
    (root / rel).write_bytes(bytes(data))
    assert [r for r, _ in gen.drift(root)] == [rel]
    assert gen.main(["--check"], root=root) == 1


def test_a_missing_generated_file_is_drift(tmp_path):
    root = copy_outputs(tmp_path)
    (root / "docs" / "REFUSALS.md").unlink()
    assert gen.drift(root) == [("docs/REFUSALS.md", "missing; run --write")]


def test_the_instruments_check_fails_on_a_wrong_checkout(tmp_path):
    r = subprocess.run([sys.executable, "-I", str(ROOT / "tools" / "check_instruments.py"), str(tmp_path)],
                       capture_output=True, text=True)
    assert r.returncode == 1 and "0 of 5 instruments reproduced" in r.stdout


def test_every_privacy_alternative_has_its_own_plant_and_every_plant_names_one():
    names = [n for _, n, _ in privacy.ALTERNATIVES]
    assert len(names) == len(set(names))
    assert set(names) == set(privacy.PLANTS)


@pytest.mark.parametrize("name", sorted(privacy.PLANTS))
def test_each_privacy_plant_is_caught_by_its_own_alternative(name):
    assert any(n == name for _, n, _ in privacy.findings(privacy.PLANTS[name], {name}))


def test_the_privacy_gate_finds_nothing_in_text_without_a_plant():
    text = ("moth_quantum_files_read, /docs/studies/qro0/, noreply@anthropic.com, user@example.org, "
            "C:\\Users\\<name>\\x, /home/{user}/x, /c/Users/$USER/x, C:\\Users\\%USERNAME%\\x")
    assert privacy.findings(text) == []
