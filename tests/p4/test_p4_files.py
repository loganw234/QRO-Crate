"""What P4 owns is written the way this repository writes its files: LF line ends and nothing else (`.gitattributes` is
`* -text`, so git converts nothing, and a file that a tool on Windows rewrote with CRLF is committed with it); the library
and the tool in ASCII, and no control character but the line feed anywhere; no file in the tree that is binary to the
privacy gate; and the parcel's names, which the registry holds, in the names the registry expects.

(A Python script run on Windows that reads a file and writes it back through `Path.write_text` writes CRLF. This was found
the hard way, in this build, in every file such a script touched.)"""
import re
import subprocess
from pathlib import Path

import pytest
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


def pieces(*parts):
    """A spelling joined at run time: written whole in this file, it would be one of the modules the guard below fails."""
    return "".join(parts)


# Every way a test of P4's could make a junction or a link: the two helpers of p4_sweeps.py, and the calls and the command they make
# it with (the seventh verifier's note 3: the guard read the first alone).
SPELLINGS = (pieces("link_dir", "("), pieces("link_at", "("), pieces("_winapi.", "CreateJunction", "("), pieces("os.", "symlink", "("),
             pieces(".symlink_", "to", "("), pieces("mk", "link"), pieces("CreateSymbolic", "Link"))
FIXTURE = re.compile(r"@pytest\.fixture\(autouse=True\)\ndef \w+\(tmp_path\):\n(?:    .*\n)*?    yield\n    remove_links_under\(tmp_path\)\n")


def spellings_in(text):
    """The ways of making a junction or a link that `text` holds."""
    return [s for s in SPELLINGS if s in text]


def unguarded(directory):
    """[(module, its spellings)] for each test module of `directory` that makes a junction or a link, by any of SPELLINGS, and has no
    autouse fixture that ends every test, passed or failed, with the links under its folder removed."""
    out = []
    for p in sorted(Path(directory).glob("test_*.py")):
        text = p.read_text(encoding="utf-8")
        if spellings_in(text) and not FIXTURE.search(text):
            out.append((p.name, spellings_in(text)))
    return out


GUARDED = ("p4", "p4shacl")          # the directories of tests under tests/ that the guard reads


def guard_failures(tests):
    """{directory: unguarded(directory)} for each directory of GUARDED under `tests` that holds a module the guard fails."""
    return {d: found for d in GUARDED if (found := unguarded(Path(tests) / d))}


def test_every_test_module_that_makes_a_junction_or_a_link_removes_what_a_failing_test_strands_with_a_fixture():
    """P4's sixth verifier, note 1 (ruled in on 2026-10-31T05:26:29Z), and the seventh's note 3 (ruled for P4.2): a failing test
    strands the junction it made, and on the owner's machine a junction whose target is later removed cannot be removed
    (remove_links_under in tests/p4/p4_helpers.py says why). So each module of tests that makes a junction or a link, by any way a
    test could (SPELLINGS), has an autouse fixture that ends every test, passed or failed, with the links under its folder removed,
    while their targets are there. The families' staged crates are cleaned by their temporary directory, which a failing test
    leaves by its context manager, and make theirs through link_at in p4_sweeps.py: no module of theirs holds a spelling."""
    assert guard_failures(ROOT / "tests") == {}
    makers = [p.name for p in sorted((ROOT / "tests" / "p4").glob("test_p4_*.py")) if spellings_in(p.read_text(encoding="utf-8"))]
    assert makers == ["test_p4_tool.py", "test_p4_tree.py"], makers              # the guard sees the modules it should


# The ways the plants below make a link, written again and not read from SPELLINGS: a spelling taken out of SPELLINGS would take its
# plant with it, and the guard would pass the module it no longer reads.
PLANTED = (pieces("link_dir", "("), pieces("link_at", "("), pieces("_winapi.", "CreateJunction", "("), pieces("os.", "symlink", "("),
           pieces(".symlink_", "to", "("), pieces("mk", "link"), pieces("CreateSymbolic", "Link"))


def test_the_ways_the_guard_reads_are_the_ways_that_are_planted():
    assert sorted(SPELLINGS) == sorted(PLANTED)
    assert sorted(GUARDED) == ["p4", "p4shacl"]                  # and the directories it reads are the two the plants are put in


@pytest.mark.parametrize("directory", ("p4", "p4shacl"))                  # written again, and not read from GUARDED (the first verifier's G11)
@pytest.mark.parametrize("spelling", PLANTED)
def test_the_guard_fails_a_planted_module_that_makes_a_link_by_each_spelling_and_passes_it_with_the_fixture(
        tmp_path, spelling, directory):
    """The guard watched failing on its plant, for each way of making a link and in each directory of tests it reads (tests/p4shacl
    as well as tests/p4: the first verifier found that no planted module stood there, so that a guard which read tests/p4 alone
    passed): a module with that spelling and no fixture, one with a fixture that is not autouse (with arguments, and bare), and one
    with an autouse fixture that removes nothing are failed; with the fixture it is passed; and a module with no spelling is passed."""
    body = f"def test_x(tmp_path):\n    made = {spelling}tmp_path)\n"
    at = chr(64)                                        # not written in the text: a letter before an at sign and a dotted name is an address
    fixture = f"import pytest\n\n\n{at}pytest.fixture(autouse=True)\ndef no_link_is_stranded(tmp_path):\n    yield\n    remove_links_under(tmp_path)\n\n\n"
    plain = fixture.replace("autouse=True", "scope='function'")
    bare = fixture.replace("(autouse=True)", "")
    inert = fixture.replace("remove_links_under(tmp_path)", "pass")
    (tmp_path / directory).mkdir()
    plant = tmp_path / directory / "test_p4_plant.py"
    plant.write_text(body, encoding="utf-8")
    failed = {directory: [("test_p4_plant.py", [spelling])]}
    assert guard_failures(tmp_path) == failed
    for wrong in (plain, bare, inert):
        plant.write_text(wrong + body, encoding="utf-8")
        assert guard_failures(tmp_path) == failed, wrong
    plant.write_text(fixture + body, encoding="utf-8")
    assert guard_failures(tmp_path) == {}
    plant.write_text("def test_x(tmp_path):\n    assert tmp_path\n", encoding="utf-8")
    assert guard_failures(tmp_path) == {}


def test_the_tree_holds_no_bytecode_p4_wrote_into_a_directory_git_would_commit():
    done = subprocess.run(["git", "-C", str(ROOT), "ls-files", "-co", "--exclude-standard", "-z"], capture_output=True)
    listed = [x.decode("utf-8") for x in done.stdout.split(b"\0") if x]
    assert not [x for x in listed if x.endswith((".pyc", ".pyo"))]
    assert all(Path(ROOT, x).is_file() for x in listed if x.startswith(tuple("/".join(p) for p in (("qro", "p4_"), ("tools", "gen_profile"), ("tests", "p4")))))
