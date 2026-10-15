"""The custody log and the audit record (study QRO-0, section 9.2): the chain, the head, the withdrawal line, and
the stated limits, each shown."""
import hashlib
import json

import pytest

from qro import canonical, custody
from qro.refusal import Refused

A, B = "a" * 64, "b" * 64


def log(*events):
    data = b""
    for event, fields in events:
        data += custody.line(data, event, **fields)
    return data


def got(crate, at, src="withheld"):
    return ("received", {"crate": crate, "at": at, "from": src})


def gone(crate, at):
    return ("withdrawn", {"crate": crate, "at": at, "reason": "it carried an identifier rule 3 forbids"})


def record(head):
    return custody.record(auditor="withheld", checker="qro 0.1.0", checkerCommit="unknown", crate=A,
                          date="2026-10-14", independence="producer-build", logHead=head, signature="none",
                          stages=["crate-only"], trustedTime="none", verdict="accepted")


def test_the_first_lines_predecessor_is_the_empty_strings_sha256():
    first = json.loads(log(got(A, "2026-10-14T01:00:00Z")))
    assert first["prev"] == hashlib.sha256(b"").hexdigest() == custody.EMPTY


def test_an_empty_log_has_head_none_which_pins_nothing():
    assert custody.check_log(b"") == "none"
    assert custody.check_record(record("none"), b"")["logHead"] == "none"


def test_the_head_is_the_last_lines_sha256():
    data = log(got(A, "2026-10-14T01:00:00Z"), got(B, "2026-10-14T02:00:00Z"))
    assert custody.check_log(data) == hashlib.sha256(custody.lines(data)[-1]).hexdigest()


def test_a_withdrawal_appended_keeps_the_chain_whole():
    data = log(got(A, "2026-10-14T01:00:00Z"), got(B, "2026-10-14T02:00:00Z"), gone(A, "2026-10-14T03:00:00Z"))
    head = custody.check_log(data)
    assert custody.check_record(record(head), data)["verdict"] == "accepted"


def test_an_audit_record_pins_the_log_up_to_its_head():
    """Then a later edit, drop or rewrite at or before the head shows (section 9.2)."""
    data = log(got(A, "2026-10-14T01:00:00Z"), got(B, "2026-10-14T02:00:00Z"))
    rec = record(custody.check_log(data))
    rewritten = log(got(A, "2026-10-14T01:30:00Z"), got(B, "2026-10-14T02:00:00Z"))     # rewritten, rehashed
    with pytest.raises(Refused) as r:
        custody.check_record(rec, rewritten)
    assert r.value.name == "custody-head"


def test_stated_limit_the_last_line_and_the_tail_show_nothing_in_the_log_itself():
    """The last line has no next line: editing it, or rewriting the tail and recomputing, passes the chain."""
    data = log(got(A, "2026-10-14T01:00:00Z"), got(B, "2026-10-14T02:00:00Z"))
    first = custody.lines(data)[0]
    edited_tail = first + custody.line(first, "received", crate=B, at="2026-10-14T02:30:00Z", **{"from": "withheld"})
    assert custody.check_log(edited_tail) != custody.check_log(data)


def test_stated_limit_lines_after_the_head_stay_uncovered():
    data = log(got(A, "2026-10-14T01:00:00Z"))
    rec = record(custody.check_log(data))
    later = data + custody.line(data, "received", crate=B, at="2026-10-14T02:00:00Z", **{"from": "withheld"})
    assert custody.check_record(rec, later)["crate"] == A


@pytest.mark.parametrize("bad", [
    b'{"at":"2026-10-14T01:00:00Z","crate":"' + A.encode() + b'","event":"received","from":"withheld","prev":"'
    + custody.EMPTY.encode() + b'"}',                                                         # no final LF
    b'{"at": "2026-10-14T01:00:00Z"}\n',                                                      # not canonical
    canonical.compact({"at": "2026-10-14T01:00:00Z", "crate": A, "event": "moved", "prev": custody.EMPTY}),
    canonical.compact({"at": "2026-10-14T01:00:00Z", "crate": A, "event": "received", "from": "withheld",
                       "prev": custody.EMPTY, "user": "x"}),                                  # a field too many
])
def test_a_line_out_of_its_spelling_is_refused(bad):
    with pytest.raises(Refused) as r:
        custody.check_log(bad)
    assert r.value.name == "spelling"


def test_an_audit_record_out_of_its_spelling_is_refused():
    rec = json.loads(record("none"))
    rec["verdict"] = "fine"
    with pytest.raises(Refused) as r:
        custody.check_record(canonical.dumps(rec), b"")
    assert r.value.name == "spelling"


@pytest.mark.parametrize("stages", [["crate-only", "crate-only"], ["crate-only", "anchors"], [], "crate-only", [1],
                                    [["crate-only"]],
                                    ["crate-only", "audit"], 5],
                         ids=["a stage twice", "unsorted", "none", "a string", "a number", "a list in the list",
                              "a word of no set", "a number for the list"])
def test_an_audit_records_stages_are_a_sorted_list_of_distinct_words(stages):
    """P0's verifier, round 2: no test planted a stage twice, and its rule could go unwatched. A number for the list
    is refused, never a crash (P0.1's verifier, round 1, 4.2)."""
    rec = json.loads(record("none"))
    rec["stages"] = stages
    with pytest.raises(Refused) as r:
        custody.check_record(canonical.dumps(rec), b"")
    assert (r.value.name, r.value.where.split()[-1]) == ("spelling", "stages")


def test_an_audit_records_every_stage_in_sorted_order_is_accepted():
    """P0.1's verifier, round 1, 4.2: held to sorted order, never to a set's, which changes with the hash seed."""
    from qro import vocabulary as V
    rec = json.loads(record("none"))
    rec["stages"] = sorted(V.WORDS["audit-stage"])
    custody.check_record(canonical.dumps(rec), b"")


def test_stated_limit_a_line_dated_in_the_future_is_accepted():
    """No clock is consulted: `at` is held to its spelling only (qro/custody.py's docstring)."""
    data = log(got(A, "2099-01-01T00:00:00Z"))
    assert custody.check_log(data) == hashlib.sha256(data).hexdigest()


def test_a_record_is_held_to_a_log_whose_chain_breaks_after_its_head():
    """Round 3, row 1: check_record checks the whole log, not only the line its head names."""
    data = log(got(A, "2026-10-14T01:00:00Z"), got(B, "2026-10-14T02:00:00Z"))
    first, second = custody.lines(data)
    broken = first + canonical.compact(dict(json.loads(second), prev="c" * 64))
    rec = record(hashlib.sha256(first).hexdigest())
    with pytest.raises(Refused) as r:
        custody.check_record(rec, broken)
    assert (r.value.name, r.value.where) == ("custody-chain", "log line 2")
