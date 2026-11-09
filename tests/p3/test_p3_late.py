"""`selector-late` (qro/p3_declaration.py's `late`; P3's design, item 1, "How before is held"): a comparison is labelled
exploratory, kept and never refused, unless the declaration names a copy of a pre-registration whose bytes hold the plan's
digest as a whole token, 64 lowercase hex digits neither preceded nor followed by a hex digit of either case."""
import pytest

from qro import p3_declaration as D

DIGEST = "0123456789abcdef" * 4


@pytest.mark.parametrize("prereg, word", [
    (None, "selector-late"),
    (b"", "selector-late"),
    (b"a plan with no digest in it\n", "selector-late"),
    (f"plan {DIGEST}\n".encode(), "none"),
    (DIGEST.encode(), "none"),
    (f"({DIGEST})".encode(), "none"),
    (f"plan:{DIGEST}.".encode(), "none"),
    (f"before\n{DIGEST}\nafter".encode(), "none"),
    (f"0{DIGEST}".encode(), "selector-late"),
    (f"{DIGEST}f".encode(), "selector-late"),
    (f"A{DIGEST}".encode(), "selector-late"),
    (f"{DIGEST}F".encode(), "selector-late"),
    (DIGEST.upper().encode(), "selector-late"),
    (DIGEST[:-1].encode(), "selector-late"),
    (f"x{DIGEST[:32]} {DIGEST[32:]}x".encode(), "selector-late"),
    ((DIGEST + DIGEST).encode(), "selector-late"),
    (f"{DIGEST}g".encode(), "none"),
    (b"\xff\xfe" + DIGEST.encode() + b"\x00", "none"),
], ids=["no pre-registration", "an empty one", "no digest", "the digest as a word", "the digest alone",
        "in brackets", "after a colon, before a dot", "on its own line", "a hex digit before", "a hex digit after",
        "an upper-case hex digit before", "an upper-case hex digit after", "the digest in upper case", "one short",
        "split by a space", "twice with no gap: a run of 128", "a letter past f after", "any bytes around it"])
def test_late_is_none_only_where_the_digest_is_a_whole_token(prereg, word):
    assert D.late(DIGEST, prereg) == word


def test_another_plans_digest_in_the_pre_registration_is_late():
    other = "f" * 64
    assert D.late(DIGEST, f"plan {other}\n".encode()) == "selector-late"
