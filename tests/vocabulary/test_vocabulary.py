"""The vocabulary table passes its own sanity check (each contradiction qro/vocabulary.py's sanity() names), pins
RO-Crate's context, and every refusal name a Refused(...) call in the package spells is one of its rows, with
the scan's stated limit (study QRO-0, rule 9 and section 13's P0).
"""
import ast
import hashlib
import json
from pathlib import Path

import pytest

from qro import reader
from qro import vocabulary as V
from qro.refusal import Refused

ROOT = Path(__file__).resolve().parents[2]


def test_the_table_is_sane():
    assert V.sanity() == []


def test_the_table_can_fail_its_sanity(monkeypatch):
    bad = V.Term("qro:x", "CHECKED", "digest", False, (), "body", None, "P0", "a CHECKED term with no step")
    monkeypatch.setattr(V, "TERMS", V.TERMS + (bad,))
    assert any("qro:x" in p for p in V.sanity())


def test_a_step_given_two_parcels_fails_the_sanity_check(monkeypatch):
    """A step's refusals name the one parcel that may register it (checker.load, P0.1)."""
    bad = V.Refusal("zz-second-owner", "step 4", "refused", "P2", "a second parcel's refusal at step 4")
    monkeypatch.setattr(V, "REFUSALS", V.REFUSALS + (bad,))
    assert V.sanity() == ["refusal zz-second-owner: step 4 is P1's, and this names P2"]


def test_rocrates_context_is_the_pinned_copy():
    data = (Path(V.__file__).parent / V.ROCRATE_CONTEXT_FILE).read_bytes()
    assert hashlib.sha256(data).hexdigest() == V.ROCRATE_CONTEXT_SHA256
    assert len(reader.rocrate_terms()) == 3069 and "keywords" in reader.rocrate_terms()
    assert not any(k.startswith(V.PREFIX + ":") for k in reader.rocrate_terms())


def raised_names(root):
    """Every name a Refused(...) call in the package can raise, read from its syntax tree: a constant, or each
    branch of a conditional. Anything else is returned as "<dynamic>", which is refused. The static half of the
    guarantee whose runtime half is Refused's own KeyError (P0's verifier, N5: a line scan missed reformatted
    calls). A stated limit (P0's verifier, round 2): the constructor under another name (`R = Refused`) is not
    seen here, and its KeyError fires only when that line runs."""
    out = set()

    def names(node):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return {node.value}
        if isinstance(node, ast.IfExp):
            return names(node.body) | names(node.orelse)
        return {"<dynamic>"}
    for f in sorted((root / "qro").glob("*.py")):
        for node in ast.walk(ast.parse(f.read_text(encoding="utf-8"))):
            if isinstance(node, ast.Call) and getattr(node.func, "id", getattr(node.func, "attr", None)) == "Refused":
                out |= names(node.args[0])
    return out


def test_every_refusal_the_package_raises_is_a_row():
    raised = raised_names(ROOT)
    assert {"spelling", "raw-digest", "file-digest", "file-link", "step-unbuilt", "custody-head"} <= raised
    assert raised <= set(V.REFUSAL), raised - set(V.REFUSAL)
    assert {r.name for r in V.REFUSALS if r.owner == "P0"} <= raised, "every P0 refusal has a raise site"


def test_every_p0_term_is_exercised(tmp_path):
    """The vocabulary walked both ways (P0's verifier's notes): every term of P0's is read in the twin, or planted
    by name in a test; every other owner's term is pending its parcel. A stated limit (P0's verifier, round 2):
    "planted by name" is the quoted name found in a test file's text, not a test shown to read it."""
    from qro import fixture
    md = json.loads((fixture.make(tmp_path / "c") / "ro-crate-metadata.json").read_bytes())
    used = {k for e in md["@graph"] for k in e}
    tests = "".join(f.read_text(encoding="utf-8") for f in (ROOT / "tests").rglob("test_*.py"))
    unexercised = [t.key for t in V.TERMS if t.owner == "P0" and t.key not in used and f'"{t.key}"' not in tests]
    assert unexercised == []


def test_an_unlisted_refusal_cannot_be_raised():
    with pytest.raises(KeyError):
        Refused("no-such-refusal", "here", "never")


def test_no_term_rides_on_rocrates_context_unkinded():
    """Every RO-Crate term the table uses is one RO-Crate's context defines; every other is the profile's."""
    for t in V.TERMS:
        assert t.key.startswith(V.PREFIX + ":") or t.key in reader.rocrate_terms(), t.key
    for t in V.TYPES:
        assert t.key.startswith(V.PREFIX + ":") or t.key in reader.rocrate_terms(), t.key


def test_two_qro_names_equal_but_for_case_fail_the_sanity_check(monkeypatch):
    """GitHub lowercases a page's anchors, so a term and a type equal but for case share one (P4's design, found 8;
    P2's, found 4; P0.3)."""
    monkeypatch.setattr(V, "TYPES", V.TYPES + (V.Type("qro:Shots", "P0", "a type spelt as a term is"),))
    assert V.sanity() == ["qro:Shots: equal but for case to qro:shots, so the two share an anchor"]


def test_each_profiles_contextual_entity_is_the_tables_and_its_version_its_iris():
    """P4's design, R3 (P0.3): Process Run Crate's version is read from its IRI, never written twice."""
    want = {V.PROFILE: (V.PROFILE_NAME, V.PROFILE_VERSION), V.PROCESS_RUN_CRATE: (V.PRC_NAME, "0.6")}
    got = {e["@id"]: (e["name"], e["version"]) for e in V.profile_entities()}
    assert got == want and [e["@id"] for e in V.profile_entities()] == sorted(want)
    assert all(e["@type"] == ["CreativeWork", "Profile"] and len(e) == 4 for e in V.profile_entities())


def test_a_term_and_a_type_of_one_name_fail_the_sanity_check(monkeypatch):
    """They share an anchor too, though no two rows of one kind do (P0.3's verifier, round 1)."""
    monkeypatch.setattr(V, "TERMS", V.TERMS + (V.Term("qro:Question", "REPORTED", "text", False, (), "body", None,
                                                      "P0", "a term spelt as a type is"),))
    assert V.sanity() == ["qro:Question: both a term and a type, so the two share an anchor"]
