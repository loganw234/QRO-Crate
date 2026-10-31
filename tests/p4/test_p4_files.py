"""What P4 owns is written the way this repository writes its files: LF line ends and nothing else (`.gitattributes` is
`* -text`, so git converts nothing, and a file that a tool on Windows rewrote with CRLF is committed with it); the library
and the tool in ASCII, and no control character but the line feed anywhere; no file in the tree that is binary to the
privacy gate; and the parcel's names, which the registry holds, in the names the registry expects.

(A Python script run on Windows that reads a file and writes it back through `Path.write_text` writes CRLF. This was found
the hard way, in this build, in every file such a script touched.)"""
import re
import subprocess
from pathlib import Path

from p4_helpers import ROOT

def parts(*names):
    """Paths as patterns, joined at run time: a path written whole in a source file is one the documents' gate looks for."""
    return ["/".join(n) for n in names]


OWNED = parts(("qro", "p4_*.py"), ("tools", "gen_profile.py"), ("tests", "p4", "*.py"), ("tests", "p4shacl", "*"),
              ("docs", "P4.md"), ("profile", "**", "*"))
ASCII_ONLY = parts(("qro", "p4_*.py"), ("tools", "gen_profile.py"), ("tests", "p4shacl", "*.py"), ("tests", "p4shacl", "*.txt"),
                   ("profile", "**", "*"))


def owned():
    out = set()
    for pattern in OWNED:
        out |= {p for p in ROOT.glob(pattern) if p.is_file() and "__pycache__" not in p.parts}
    return sorted(out)


def test_every_file_p4_owns_has_lf_line_ends_and_no_other_control_character():
    files = owned()
    assert len(files) >= 30
    for p in files:
        data = p.read_bytes()
        rel = p.relative_to(ROOT).as_posix()
        assert b"\r" not in data, f"{rel}: a carriage return"
        assert not [b for b in data if b < 32 and b not in (9, 10)] and b"\x7f" not in data, f"{rel}: a control character"
        assert data.endswith(b"\n") or not data, f"{rel}: no final line feed"


def test_the_library_the_tool_the_engine_stage_and_the_generated_files_are_ascii():
    seen = 0
    for pattern in ASCII_ONLY:
        for p in ROOT.glob(pattern):
            if p.is_file() and "__pycache__" not in p.parts:
                assert p.read_bytes().isascii(), p.relative_to(ROOT).as_posix()
                seen += 1
    assert seen >= 20


def test_no_file_p4_owns_is_binary_to_the_privacy_gate():
    for p in owned():
        assert b"\0" not in p.read_bytes()[:4096], p.relative_to(ROOT).as_posix()


def test_no_template_token_is_left_in_a_file_p4_owns():
    """P4's third verifier, note 1: a docstring of the sweeps ended with the cost token of a template that was never filled: an
    at sign, three capital letters or more, an at sign."""
    for p in owned():
        found = re.findall(r"@[A-Z]{3,}@", p.read_text(encoding="utf-8"))
        assert not found, f"{p.relative_to(ROOT).as_posix()}: {found}"


def test_the_tests_of_the_parcel_are_named_as_the_registry_holds_them():
    for d, prefix in (("tests/p4", "p4"), ("tests/p4shacl", "p4shacl")):
        for p in (ROOT / d).rglob("*.py"):
            assert re.fullmatch(rf"(test_)?{prefix}_[A-Za-z0-9_]+\.py", p.name), p.name
    names = [p.name for p in (ROOT / "tests").rglob("test_p4*.py")]
    assert len(names) == len(set(names))


def test_a_helper_names_no_function_test_and_no_class_Test_for_pytest_would_collect_it():
    for d in ("tests/p4", "tests/p4shacl"):
        for p in (ROOT / d).glob("*.py"):
            if not p.name.startswith("test_"):
                assert not re.search(r"^(def test|class Test)", p.read_text(encoding="utf-8"), re.M), p.name


def test_every_test_module_that_makes_a_junction_removes_what_a_failing_test_strands_with_a_fixture():
    """P4's sixth verifier, note 1 (ruled in on 2026-10-31T05:26:29Z): a failing test strands the junction it made, and on the
    owner's machine a junction whose target is later removed cannot be removed (remove_links_under in tests/p4/p4_helpers.py says
    why). So each module of tests that makes one with link_dir has an autouse fixture that ends every test, passed or failed, with
    the links under its folder removed, while their targets are there. The families' staged crates are cleaned by their temporary
    directory, which a failing test leaves by its context manager, and make theirs through link_at, not link_dir."""
    call = "link_dir" + "("                                                      # not written whole: this file would be one of them
    makers = [p.name for p in sorted((ROOT / "tests" / "p4").glob("test_p4_*.py")) if call in p.read_text(encoding="utf-8")]
    assert makers == ["test_p4_tool.py", "test_p4_tree.py"], makers              # a module that gains a junction joins the guard
    fixture = re.compile(r"@pytest\.fixture\(autouse=True\)\ndef \w+\(tmp_path\):\n(?:    .*\n)*?    yield\n    remove_links_under\(tmp_path\)\n")
    for name in makers:
        assert fixture.search((ROOT / "tests" / "p4" / name).read_text(encoding="utf-8")), name


def test_the_tree_holds_no_bytecode_p4_wrote_into_a_directory_git_would_commit():
    done = subprocess.run(["git", "-C", str(ROOT), "ls-files", "-co", "--exclude-standard", "-z"], capture_output=True)
    listed = [x.decode("utf-8") for x in done.stdout.split(b"\0") if x]
    assert not [x for x in listed if x.endswith((".pyc", ".pyo"))]
    assert all(Path(ROOT, x).is_file() for x in listed if x.startswith(tuple("/".join(p) for p in (("qro", "p4_"), ("tools", "gen_profile"), ("tests", "p4")))))
