"""P1's adapter against the real checkout of moth-quantum named by QRO_MOTH_ROOT: it reads that checkout only if it is the
checkout the adapter was written for, clean at 3a73823, and it refuses to build into it, or into this repository, or into a
directory that holds something. (The refusals of a checkout that is not that one, and of a directory that is not empty, are
tests/p1/test_p1_adapter.py's, on small stand-ins; here is the real one.)"""
import pytest

import p1crates_support as S
from qro import p1_adapter


def test_the_checkout_named_is_moth_quantum_clean_at_the_commit_the_adapter_reads():
    p1_adapter.check_moth(S.MOTH)
    head = p1_adapter._git(S.MOTH, "rev-parse", "HEAD")
    assert head.startswith(p1_adapter.MOTH_COMMIT) and p1_adapter._git(S.MOTH, "status", "--porcelain") == ""


def test_every_file_the_plan_takes_from_the_real_checkout_is_the_commits_own_by_gits_hash_of_a_blob():
    """The build's rule (`hold_to_head`: a regular file of HEAD's tree, and that blob's bytes), asked of the real checkout alone,
    read only: the 930 files the IBM crate takes from it and the 30 the Atlas crate takes (the licence, the 928 IBM records of
    2026-10-05, the source circuit, the 28 Atlas files of the two days and the vector: 958 in all, MEASURED by the lead with
    `core.autocrlf` true here). The real builds, which the other tests of this stage make, are built under the same rule."""
    head = p1_adapter.check_moth(S.MOTH)
    tree = p1_adapter.head_tree(S.MOTH, head)
    counts = {}
    for kind in ("ibm", "atlas"):
        taken = [(src, p1_adapter._in_checkout(src, S.MOTH)) for _, src in p1_adapter.plan(kind, S.MOTH, S.ROOT / "records", False)]
        taken = [(src, held) for src, held in taken if held is not None]
        for src, held in taken:
            p1_adapter.hold_to_head(S.MOTH, tree, held, src.read_bytes())
        counts[kind] = len(taken)
    assert counts == {"ibm": 930, "atlas": 30}


def test_the_adapter_will_not_build_into_the_checkout_or_into_this_repository_by_any_spelling(tmp_path):
    """Asked of the out guard alone, `check_out`, so that a guard that regressed builds nothing, in the real checkout least
    of all (P1.2's fourth verifier). The whole command on outs inside either tree is tests/p1/test_p1_adapter.py's, on
    directories of its own. The spellings: plain, and on Windows the extended-length prefix with backslashes and with
    forward slashes. The control: an out outside both passes."""
    import os
    for parent, words in ((S.MOTH, "inside the checkout"), (S.ROOT, "inside this repository")):
        plain = parent / "adapter-built-crate"
        outs = [str(plain)]
        if os.name == "nt":
            outs += ["\\\\?\\" + str(plain), "//?/" + str(plain).replace("\\", "/")]
        for out in outs:
            with pytest.raises(p1_adapter.AdapterError, match=words):
                p1_adapter.check_out(out, S.MOTH)
        assert not plain.exists()
    p1_adapter.check_out(tmp_path / "out", S.MOTH)
    assert p1_adapter._git(S.MOTH, "status", "--porcelain") == ""


def test_the_adapter_will_not_build_into_a_directory_that_holds_something(tmp_path):
    (tmp_path / "keep.txt").write_bytes(b"mine")
    done = S.process(["ibm", "--moth", str(S.MOTH), "--out", str(tmp_path)])
    assert (done.returncode, done.stdout) == (2, "") and "not an empty directory" in done.stderr
    assert [p.name for p in tmp_path.iterdir()] == ["keep.txt"]
