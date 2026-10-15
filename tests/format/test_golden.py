"""The canonical bytes held to golden copies (P0's verifier, N1: six mutants of the canonical rules survived every
test, because the writer and the reader share qro/canonical.py and moved together).

tests/format/golden/ holds bytes written once and kept: the twin's metadata, its body and identity; a custody log
of three lines and its head; an audit record. Each test regenerates one with the code and compares bytes, and
holds the golden bytes to the rules by means independent of qro/canonical.py: hashlib for every digest, the json
module's key order and a line scan for the layout. A deliberate change to the canonical form changes these files
by hand, in its own commit, with its reason in the ledger.
"""
import hashlib
import json
import re
from pathlib import Path

from qro import canonical, custody, fixture

GOLDEN = Path(__file__).resolve().parent / "golden"
A, B = "a" * 64, "b" * 64


def golden(name):
    return (GOLDEN / name).read_bytes()


def keys_sorted(data):
    """Every object's keys in code-point order, as the json module reads them: independent of the writer."""
    bad = []

    def hook(pairs):
        keys = [k for k, _ in pairs]
        if keys != sorted(keys):
            bad.append(keys)
        return dict(pairs)
    json.loads(data, object_pairs_hook=hook)
    return not bad


def test_the_twins_metadata_is_its_golden_copy(tmp_path):
    assert (fixture.make(tmp_path / "c") / canonical.DESCRIPTOR).read_bytes() == golden("twin-metadata.json")


def test_the_golden_metadata_keeps_the_rules():
    data = golden("twin-metadata.json")
    text = data.decode("ascii")
    assert text.endswith("\n") and "\r" not in text and "\t" not in text
    for line in text.splitlines():
        indent = len(line) - len(line.lstrip(" "))
        assert indent % 2 == 0 and line == line.rstrip(), repr(line)
        if re.match(r'\s*"', line) and '":' in line:
            assert '": ' in line, repr(line)
    assert keys_sorted(data)


def test_the_twins_body_and_identity_are_their_golden_copies():
    body = golden("twin-body.json")
    md = json.loads(golden("twin-metadata.json"))
    assert canonical.dumps(canonical.body(md)) == body
    assert hashlib.sha256(body).hexdigest() == golden("twin-identity.txt").decode("ascii").strip()
    assert canonical.body_digest(md) == golden("twin-identity.txt").decode("ascii").strip()
    assert b"qro:writtenAt" not in body and b"datePublished" not in body


def log():
    data = b""
    for event, fields in (("received", {"crate": A, "at": "2026-10-14T01:00:00Z", "from": "withheld"}),
                          ("received", {"crate": B, "at": "2026-10-14T02:00:00Z", "from": "a-custodian"}),
                          ("withdrawn", {"crate": A, "at": "2026-10-14T03:00:00Z",
                                         "reason": "it carried an identifier rule 3 forbids"})):
        data += custody.line(data, event, **fields)
    return data


def test_the_custody_log_is_its_golden_copy_and_its_chain_rederives():
    data = golden("custody.log")
    assert log() == data
    prev = hashlib.sha256(b"").hexdigest()
    for line in data.split(b"\n")[:-1]:
        obj = json.loads(line)
        assert obj["prev"] == prev and b": " not in line and b", " not in line and keys_sorted(line)
        prev = hashlib.sha256(line + b"\n").hexdigest()
    assert prev == golden("custody-head.txt").decode("ascii").strip() == custody.check_log(data)


def test_the_audit_record_is_its_golden_copy():
    head = golden("custody-head.txt").decode("ascii").strip()
    rec = custody.record(auditor="withheld", checker="qro 0.1.0", checkerCommit="unknown", crate=A,
                         date="2026-10-14", independence="producer-build", logHead=head, signature="none",
                         stages=["crate-only"], trustedTime="none", verdict="accepted")
    assert rec == golden("audit-record.json")
    assert keys_sorted(rec) and custody.check_record(rec, golden("custody.log"))["logHead"] == head
