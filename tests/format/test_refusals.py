"""Every refusal P0 owns is raised by a planted fault, by its own name, and no plant names a refusal P0 does not
own (the registry walked both ways, ParcelRound, METHOD.md section 2). Each plant is one fault in a fresh copy
of the fixture crate, which is itself accepted."""
import hashlib
import json
import os
import pathlib
import subprocess
import sys

import pytest

from qro import canonical, checker, custody, fixture
from qro import vocabulary as V
from qro.refusal import Refused

RAW, NOTES = "data/raw.counts.json", "data/notes.txt"


@pytest.fixture(autouse=True)
def registered(monkeypatch):
    monkeypatch.setattr(checker, "RAW_FORMS", {})
    monkeypatch.setattr(checker, "GENERATORS", {})
    fixture.register()


def crate(tmp_path):
    return fixture.make(tmp_path / "crate")


def edit_bytes(c, f):
    p = c / canonical.DESCRIPTOR
    p.write_bytes(f(p.read_bytes()))
    return c


def edit(c, f):
    """Change the parsed metadata with f, and write it back in canonical bytes: one fault, nothing else."""
    def apply(b):
        md = json.loads(b)
        f(md)
        return canonical.dumps(md)
    return edit_bytes(c, apply)


def reseal(c, rel):
    """Recompute a file's digest and size in the metadata, as a forger would."""
    b = (c / rel).read_bytes()
    return edit(c, lambda md: entity(md, rel).update(sha256=hashlib.sha256(b).hexdigest(), contentSize=str(len(b))))


def entity(md, i):
    return next(e for e in md["@graph"] if e["@id"] == i)


def spelling_bytes(c):
    return edit_bytes(c, lambda b: b.replace(b'"@graph": [', b'"@graph":  [', 1))


def spelling_value(c):
    return edit(c, lambda md: entity(md, RAW).update(sha256=entity(md, RAW)["sha256"].upper()))


def context(c):
    return edit(c, lambda md: md.update({"@context": [V.ROCRATE_CONTEXT, {"qro": "https://example.org/other#"}]}))


def graph_form(c):
    return edit(c, lambda md: md["@graph"].append(dict(md["@graph"][-1])))      # one @id twice


def term_unknown(c):
    return edit(c, lambda md: md["@graph"][1].update({"qro:nonesuch": "x"}))


def field_kind(c):
    return edit(c, lambda md: md["@graph"][1].update(keywords="fixture"))


def file_missing(c):
    (c / NOTES).unlink()
    return c


def file_unlisted(c):
    (c / "data" / "stray.txt").write_bytes(b"a file no entity lists\n")
    return c


def file_digest(c):
    (c / NOTES).write_bytes((c / NOTES).read_bytes().replace(b"one note", b"two note"))
    return c


def raw_digest(c):
    (c / RAW).write_bytes(canonical.compact({"00": 2, "01": 2, "11": 4}))
    return c


def raw_form(c):
    (c / RAW).write_bytes(b'{"00": 3, "01": 1, "11": 4}\n')     # the same counts, not in the form's one line
    return reseal(c, RAW)


def count_unpaid(c):
    return edit(c, lambda md: entity(md, RAW).update({"qro:shots": 9}))


def metadata_generated(c):
    return edit(c, lambda md: md["@graph"][1].update(name="a name the generator never writes"))


def step_unbuilt(c):
    return edit(c, lambda md: fixture.with_entity(md, {"@id": "#pub", "@type": "qro:Pub", "qro:commitment": "a" * 64}))     # step 4's field


LINKS = []


def link(path, target):
    """A directory link: a junction on Windows, which needs no privilege; a symbolic link elsewhere. Each is removed
    when its test ends, by unlink_made."""
    if os.name == "nt":
        import _winapi
        _winapi.CreateJunction(str(target), str(path))
    else:
        os.symlink(target, path, target_is_directory=True)
    LINKS.append(path)


def links_below(root):
    """[Path]: every link below `root` that a directory lists, found by listing each directory and never by asking the
    host what an entry is, for this machine cannot stat a junction whose target is gone (CLAUDE.md item 10), as the
    checker's question of what a listed entry is knows. A link is recorded and not followed. Copied from
    test_hostile.py, not imported: a `tests` package in site-packages shadows a helper module under tests/."""
    found, todo = [], [root]
    while todo:
        with os.scandir(todo.pop()) as entries:
            for entry in entries:
                if entry.is_symlink() or entry.is_junction():
                    found.append(pathlib.Path(entry.path))
                elif entry.is_dir(follow_symlinks=False):
                    todo.append(entry.path)
    return sorted(found)


def assert_no_link_below(root):
    """Fail if `root` still lists a link, dangling or not (P0.9; P0.8's second and third verifiers, TB: `unlink_made`
    removing nothing passed every test, and CLAUDE.md item 10 held it by text). A link that can be removed is removed
    all the same, while its target is there, so that a failing test strands nothing in pytest's temporary folder; one
    whose target is gone cannot be, on this machine, and is named."""
    left, stuck = links_below(root), []
    for path in left:
        try:
            (os.rmdir if os.name == "nt" else os.unlink)(path)
        except OSError:
            stuck.append(path)
    names = ", ".join(p.relative_to(root).as_posix() for p in left)
    assert not left, (f"the test left {len(left)} link(s) in its temporary folder, which pytest's cleanup cannot "
                      f"remove once it renames the folder (CLAUDE.md item 10): {names}; "
                      f"{len(stuck)} could not be removed here")


@pytest.fixture(autouse=True)
def no_link_left_behind(request):
    """Every test of this module: if its tmp_path still lists a link when it and its fixtures are done, it fails. The
    fixture is set up before the others, so it is torn down after theirs (unlink_made asks for it, to make it so);
    and it asks for tmp_path only of a test that has one, which is all a link could be made in."""
    root = request.getfixturevalue("tmp_path") if "tmp_path" in request.fixturenames else None
    yield
    if root is not None:
        assert_no_link_below(root)


@pytest.fixture(autouse=True)
def unlink_made(no_link_left_behind):
    """Each link a plant made, removed when its test ends, while its target is there: pytest renames an old
    temporary folder before it removes it, which leaves a link in one pointing at nothing, and on a host that opens
    no dangling link, as this machine, pytest's own cleanup cannot then remove it (P0.8's first verifier, D3;
    CLAUDE.md item 10)."""
    yield
    while LINKS:
        path = LINKS.pop()
        if path.name in os.listdir(path.parent):
            (os.rmdir if os.name == "nt" else os.unlink)(path)


def file_link(c):
    outside = c.parent / "outside"
    outside.mkdir()
    (outside / "secret.txt").write_bytes(b"a file outside the crate\n")
    link(c / "data" / "jct", outside)
    return c


PLANTS = {"spelling": spelling_value, "context": context, "graph-form": graph_form, "term-unknown": term_unknown,
          "field-kind": field_kind, "file-missing": file_missing, "file-unlisted": file_unlisted,
          "file-digest": file_digest, "raw-digest": raw_digest, "file-link": file_link, "raw-form": raw_form,
          "count-unpaid": count_unpaid, "metadata-generated": metadata_generated, "step-unbuilt": step_unbuilt}
CUSTODY = {"custody-chain", "custody-head"}           # planted by tests/custody and controls/registry.py


def test_the_twin_is_accepted(tmp_path):
    md = checker.check(crate(tmp_path))
    assert canonical.body_digest(md) == canonical.body_digest(fixture.generate(tmp_path / "crate"))


def test_every_p0_refusal_has_a_plant_and_every_plant_names_one():
    p0 = {r.name for r in V.REFUSALS if r.owner == "P0"}
    assert set(PLANTS) | CUSTODY == p0
    assert not (set(PLANTS) - p0)


@pytest.mark.parametrize("name", sorted(PLANTS))
def test_each_plant_is_refused_by_its_own_name(tmp_path, monkeypatch, name):
    """Steps 4 to 8 unbuilt by the test itself: once a parcel's steps are loaded, an earlier test in the process
    loads them, and step-unbuilt's plant met a built step 4 (the lead's simulation of P1 and P2, P0.1)."""
    monkeypatch.setattr(checker, "STEPS", {n: None for n in range(4, 9)})
    with pytest.raises(Refused) as r:
        checker.check(PLANTS[name](crate(tmp_path)))
    assert r.value.name == name, f"refused {r.value.name} at {r.value.where}: {r.value.detail}"


def test_a_byte_out_of_place_is_spelling_at_its_line(tmp_path):
    with pytest.raises(Refused) as r:
        checker.check(spelling_bytes(crate(tmp_path)))
    assert r.value.name == "spelling" and r.value.where.startswith("line ")


@pytest.mark.parametrize("data, why", [
    (b'{"a": 1, "a": 2}', "twice"), (b'{"a": NaN}', "NaN"), (b'{"a": 1e400}\n', "finite"),
    ("{\"a\": \"é\"}\n".encode("utf-8"), "ASCII"), (b"[]", "canonical")])
def test_the_bytes_refused_before_anything_is_read(data, why):
    from qro import reader
    with pytest.raises(Refused) as r:
        reader.read(data)
    assert r.value.name == "spelling", why


def test_steps_4_to_8_each_refuse_their_fields_until_built(tmp_path, monkeypatch):
    """Unbuilt by the test itself, so it holds once the parcels' steps are loaded too (P0.1)."""
    monkeypatch.setattr(checker, "STEPS", {n: None for n in range(4, 9)})
    fields = {4: ("#pub", "qro:Pub", "qro:commitment", "a" * 64),
              8: ("#snapshot", "qro:Snapshot", "qro:valuesDigest", "b" * 64)}
    for n, (i, t, k, v) in fields.items():
        c = edit(fixture.make(tmp_path / f"c{n}"), lambda md: fixture.with_entity(md, {"@id": i, "@type": t, k: v}))
        with pytest.raises(Refused) as r:
            checker.check(c)
        assert (r.value.name, r.value.detail) == ("step-unbuilt", f"step {n} is not built yet")


def test_a_raw_form_or_generator_with_no_reader_is_step_unbuilt(tmp_path, monkeypatch):
    c = crate(tmp_path)
    monkeypatch.setattr(checker, "RAW_FORMS", {})
    with pytest.raises(Refused) as r:
        checker.check(c)
    assert r.value.name == "step-unbuilt" and "raw form" in r.value.detail
    fixture.register()
    monkeypatch.setattr(checker, "GENERATORS", {})
    with pytest.raises(Refused) as r:
        checker.check(c)
    assert r.value.name == "step-unbuilt" and "generator" in r.value.detail


def test_the_steps_run_in_order(tmp_path):
    """A crate with two faults is refused by the earlier step's name."""
    c = raw_digest(crate(tmp_path))
    edit(c, lambda md: entity(md, RAW).update({"qro:shots": 9}))
    with pytest.raises(Refused) as r:
        checker.check(c)
    assert r.value.name == "raw-digest"


def test_custody_refusals_are_planted_elsewhere():
    from controls.registry import CONTROLS
    assert CUSTODY <= {c.refusal for c in CONTROLS if c.owner == "P0"}
    assert custody.EMPTY == "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"


# -- each profile's contextual entity (P4's design, found 1, R3 and D10; P0.3) -----------------------------------
PRC = V.PROCESS_RUN_CRATE
OTHER = {"@id": "https://example.org/another-profile", "@type": ["CreativeWork", "Profile"], "name": "another",
         "version": "1.0"}


@pytest.mark.parametrize("fault, refusal, where", [
    (lambda md: md["@graph"].remove(entity(md, V.PROFILE)), "graph-form", V.PROFILE),
    (lambda md: md["@graph"].remove(entity(md, PRC)), "graph-form", PRC),
    (lambda md: entity(md, V.PROFILE).update(version="0.2"), "context", V.PROFILE + " version"),
    (lambda md: entity(md, PRC).update(version="0.5"), "context", PRC + " version"),
    (lambda md: entity(md, V.PROFILE).pop("version"), "graph-form", V.PROFILE),
    (lambda md: entity(md, V.PROFILE).update(description="a profile"), "graph-form", V.PROFILE),
    (lambda md: entity(md, PRC).update({"@type": "Profile"}), "graph-form", PRC),
    (lambda md: fixture.with_entity(md, dict(OTHER)), "graph-form", OTHER["@id"]),
    (lambda md: entity(md, V.PROFILE).update(version="0.2", name="another"), "graph-form", V.PROFILE),
    (lambda md: entity(md, V.PROFILE).update(version=1), "graph-form", V.PROFILE),
    (lambda md: entity(md, V.PROFILE).update(version=0.1), "graph-form", V.PROFILE),
    (lambda md: fixture.with_entity(md, {"@id": "https://example.org/typed-profile-only", "@type": "Profile",
                                         "name": "x", "version": "1"}), "graph-form",
     "https://example.org/typed-profile-only")],
    ids=["this profile's entity missing", "Process Run Crate's missing", "this profile at another version",
         "Process Run Crate at another version", "no version", "a key more", "typed Profile alone",
         "a Profile entity for no profile the root conformsTo", "another version and another name",
         "a version that is no text", "a version that is a float", "a Profile entity typed Profile alone"])
def test_each_profile_the_root_conforms_to_has_its_contextual_entity_exactly(tmp_path, fault, refusal, where):
    """RO-Crate 1.3 requires a contextual entity for each profile in conformsTo, and the study's section 3 says so;
    P0 wrote none (P4's design, found 1). The reader holds both to the table's, and names another version
    `context`; a version that is no text, an integer or a float (P0.4's verifier, round 2, N5), is `graph-form`."""
    with pytest.raises(Refused) as e:
        checker.check(edit(crate(tmp_path), fault))
    assert (e.value.name, e.value.where) == (refusal, where)


def test_a_version_on_any_entity_but_a_profile_is_refused(tmp_path):
    with pytest.raises(Refused) as e:
        checker.check(edit(crate(tmp_path), lambda md: entity(md, RAW).update(version="0.1")))
    assert e.value.name == "graph-form" and e.value.where.startswith(RAW), e.value


def test_the_profiles_are_held_after_the_roots_conformsto_and_before_its_references(tmp_path):
    """The reader's order (P0.3's verifier, round 1): the root's conformsTo, then each profile's entity, then the
    references. Each crate here carries two faults, and the one first in that order is the one named."""
    def wrong_conformance(md):
        md["@graph"].remove(entity(md, V.PROFILE))
        md["@graph"][1]["conformsTo"] = [{"@id": PRC}]

    def dangling(md):
        md["@graph"].remove(entity(md, V.PROFILE))
        md["@graph"][1]["hasPart"] = sorted(md["@graph"][1]["hasPart"] + [{"@id": "data/none.txt"}],
                                            key=lambda r: r["@id"])
    def unmentioned(md):
        md["@graph"].remove(entity(md, V.PROFILE))
        fixture.with_entity(md, {"@id": "#run", "@type": "CreateAction"})

    for name, fault, where in (("a", wrong_conformance, "./ conformsTo"), ("b", dangling, V.PROFILE),
                               ("c", unmentioned, V.PROFILE)):
        with pytest.raises(Refused) as e:
            checker.check(edit(fixture.make(tmp_path / name), fault))
        assert (e.value.name, e.value.where) == ("graph-form", where), name


# -- no test of this module leaves a link behind (P0.9; P0.8's second and third verifiers, TA and TB) -------------
# The guard above (no_link_left_behind) fails a test whose tmp_path still lists a link. Its controls: what it sees,
# and `unlink_made` made to remove nothing, run as a pytest session of its own, failing the test that made a link.
def test_the_guard_sees_a_live_link_and_removes_it_leaving_its_target(tmp_path):
    (tmp_path / "a").mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "kept.txt").write_bytes(b"the target's own file\n")
    link(tmp_path / "a" / "jct", outside)
    assert links_below(tmp_path) == [tmp_path / "a" / "jct"]
    with pytest.raises(AssertionError) as e:
        assert_no_link_below(tmp_path)
    assert "left 1 link(s)" in str(e.value) and "a/jct" in str(e.value) and "0 could not be removed" in str(e.value)
    assert links_below(tmp_path) == [] and (outside / "kept.txt").read_bytes() == b"the target's own file\n"


def test_the_guard_sees_a_link_whose_target_is_gone(tmp_path):
    """On this machine such a junction cannot be stat'd, so a guard that asked the host what an entry is would see
    nothing; listing the directory finds it (CLAUDE.md item 10). It cannot be removed here until its target is made
    again, which the test then does."""
    gone = tmp_path / "gone"
    gone.mkdir()
    link(tmp_path / "jct", gone)
    gone.rmdir()
    assert links_below(tmp_path) == [tmp_path / "jct"]
    with pytest.raises(AssertionError) as e:
        assert_no_link_below(tmp_path)
    assert "left 1 link(s)" in str(e.value) and "jct" in str(e.value)
    if links_below(tmp_path):                 # one the host could not remove while its target was gone
        gone.mkdir()
        (os.rmdir if os.name == "nt" else os.unlink)(tmp_path / "jct")
        gone.rmdir()
    assert links_below(tmp_path) == []


def test_the_guard_does_not_follow_a_link(tmp_path):
    """A link to a directory that holds a link is listed once, and the one inside is found where it stands, not again
    through the first."""
    (tmp_path / "outside" / "sub").mkdir(parents=True)
    (tmp_path / "other").mkdir()
    link(tmp_path / "outside" / "sub" / "k", tmp_path / "other")
    link(tmp_path / "j", tmp_path / "outside")
    assert links_below(tmp_path) == sorted([tmp_path / "j", tmp_path / "outside" / "sub" / "k"])
    with pytest.raises(AssertionError) as e:
        assert_no_link_below(tmp_path)
    assert "left 2 link(s)" in str(e.value) and "0 could not be removed" in str(e.value)
    assert links_below(tmp_path) == []


def test_a_directory_with_no_link_in_it_passes_the_guard(tmp_path):
    (tmp_path / "plain" / "deeper").mkdir(parents=True)
    (tmp_path / "plain" / "deeper" / "file.txt").write_bytes(b"x\n")
    assert links_below(tmp_path) == []
    assert_no_link_below(tmp_path)


def planted_session(tmp_path, old, new, node):
    """This module's own text with `old` replaced by `new`, once, run as a pytest session of its own on the one test
    `node`: the result of that session, and the links it left. The session is rooted in a folder of its own, holding
    a copy of the root's pyproject.toml (the same options as a stage's, that file alone) and the module, so that its
    collection lists nothing else: pytest compares every entry of each folder between its rootdir and a test file with
    `lstat`, and a rootdir above the temporary folder made it list the shared one, where another process's folder
    removed between the listing and the `lstat` was a FileNotFoundError and an error collecting the session
    (MEASURED once in the runner, 2026-10-31). `qro` is found through PYTHONPATH, as the other process tests find it."""
    root = pathlib.Path(__file__).resolve().parents[2]
    text = pathlib.Path(__file__).read_text(encoding="utf-8")
    assert text.count(old) == 1, f"the plant's text is in this module {text.count(old)} times"
    planted = tmp_path / "planted"
    planted.mkdir()
    (planted / "pyproject.toml").write_bytes((root / "pyproject.toml").read_bytes())
    (planted / "test_planted_refusals.py").write_text(text.replace(old, new), encoding="utf-8")
    env = {k: v for k, v in os.environ.items() if k not in ("PYTEST_ADDOPTS", "PYTEST_PLUGINS", "PYTHONSAFEPATH")}
    env.update(PYTEST_DISABLE_PLUGIN_AUTOLOAD="1", PYTHONPATH=str(root))
    session = subprocess.run([sys.executable, "-m", "pytest", "-c", "pyproject.toml", "--noconftest", "--color=no",
                              "-q", "--basetemp=bt", f"test_planted_refusals.py::{node}"],
                             cwd=planted, capture_output=True, text=True, env=env)
    return session, links_below(planted)


NODE = "test_each_plant_is_refused_by_its_own_name[file-link]"


def test_an_unlink_made_that_removes_nothing_fails_the_test_that_made_a_link(tmp_path):
    """P0.8's second verifier, TB: with `unlink_made` made to remove nothing, 491 tests passed and a live junction was
    left in pytest's temporary folder. Here the same plant fails the test that made a link, as an error at its
    teardown, which is how pytest reports a fixture that fails, and leaves none behind."""
    session, left = planted_session(tmp_path, "    while " + "LINKS:", "    while " + "[]:", NODE)
    assert session.returncode == 1 and "1 passed, 1 error" in session.stdout, session.stdout[-1500:]
    assert "the test left 1 link(s) in its temporary folder" in session.stdout, session.stdout[-1500:]
    assert left == [], "the guard removed what it found"


def test_the_same_session_with_unlink_made_unplanted_passes(tmp_path):
    old = "    while " + "LINKS:"
    session, left = planted_session(tmp_path, old, old, NODE)
    assert session.returncode == 0 and "1 passed" in session.stdout, session.stdout[-1500:]
    assert left == []
