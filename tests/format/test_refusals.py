"""Every refusal P0 owns is raised by a planted fault, by its own name, and no plant names a refusal P0 does not
own (the registry walked both ways, ParcelRound, METHOD.md section 2). Each plant is one fault in a fresh copy
of the fixture crate, which is itself accepted."""
import hashlib
import json
import os

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


@pytest.fixture(autouse=True)
def unlink_made():
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
