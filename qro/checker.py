"""The checker: section 10's nine steps, in order, refusing at the first failure by name and location (study QRO-0).

P0 builds four of them:
  1. the bytes: qro/reader.py;
  2. no link anywhere in the crate, the metadata file among them (`file-link`); every listed file, and the metadata
     file, present under its exact name (`file-missing`); the walk in name order, raising on a directory it
     cannot list;
     every file present listed and reached from the root through hasPart (`file-unlisted`); every file's bytes
     held to its digest and size (`file-digest`, and `raw-digest` for a raw result);
  3. every raw result read in its raw form (`raw-form`), and every count held to what the bytes hold
     (`count-unpaid`, rule 7); then every count rule a parcel registers in COUNTS;
  9. the metadata regenerated from the records by the generator the root names, the header normalised, and
     compared byte for byte (`metadata-generated`, rule 5).
Steps 4 to 8 are the parcels'. A parcel declares its steps, raw forms' readers, count rules and generators in its
own module, qro.register_<parcel>, and load() merges them into STEPS, RAW_FORMS, COUNTS and GENERATORS (P0.1).
Where a crate holds a CHECKED field whose step is not built, a raw form with no reader, or a generator not
built, the checker refuses `step-unbuilt`: it never passes what it has not checked
("a seam's refusal belongs in every backend", ParcelRound, METHOD.md section 2). A registered reader or generator
that fails on the crate's bytes is refused by its step's name, never a crash, but for a MemoryError: that is the
host's, and the checker failing (FORMAT.md item 16). Stdlib only.
"""
import hashlib
import importlib
import importlib.util
import os
import sys
from pathlib import Path

from qro import canonical, reader
from qro import vocabulary as V
from qro.refusal import Refused

STEPS = {4: None, 5: None, 6: None, 7: None, 8: None}     # n -> fn(crate_dir, metadata), raising Refused
RAW_FORMS = {}                                           # name -> fn(bytes) -> shots, raising RawFormError
COUNTS = []                                              # fn(crate_dir, metadata), raising Refused("count-unpaid")
GENERATORS = {}                                          # name -> fn(crate_dir) -> metadata (a dict)


class RawFormError(ValueError):
    pass


class RegistrationError(Exception):
    """A parcel's module registers what is not its own to register: the checker's build is wrong, not the crate."""


def step_owners():
    """{step: the parcel whose refusals the vocabulary places at it}: steps 1, 2, 3 and 9 are P0's."""
    out = {}
    for r in V.REFUSALS:
        for part in r.where.split("; "):
            if part.startswith("step "):
                out[int(part[len("step "):])] = r.owner
    return out


def registration(parcel):
    """The module a parcel declares its checker code in: qro.register_p1 for P1."""
    return f"qro.register_{parcel.lower()}"


FIXTURE_NAMES = "qro-fixture"      # P0's fixture's raw form and generator begin so, and no parcel's may


def _register(registry, key, fn, module):
    if str(key).startswith(FIXTURE_NAMES):
        raise RegistrationError(f"{module} registers {key}, a name of P0's fixture")
    if registry.get(key) is not None and registry[key] is not fn:
        raise RegistrationError(f"{module} registers {key}, which another function already holds")
    registry[key] = fn


def _registries():
    return dict(STEPS), dict(RAW_FORMS), list(COUNTS), dict(GENERATORS)


def describe(x):
    """An exception's type and text, or its type alone where its text itself raises: written here, the text of a
    hostile exception, whose __str__ raised a Refused, escaped as a verdict (P0.1's verifier, round 3, C1)."""
    try:
        name = type(x).__name__
    except BaseException:
        name = "an exception"
    try:
        return f"{name}: {x}"
    except BaseException:
        return f"{name}, whose text cannot be read"


def _declared(module, name, parcel, owners):
    for n, fn in getattr(module, "STEPS", {}).items():
        if owners.get(n) != parcel:
            raise RegistrationError(f"{name} registers step {n}, which is {owners.get(n, 'no parcel')}'s")
        _register(STEPS, n, fn, name)
    for registry, declared in ((RAW_FORMS, "RAW_FORMS"), (GENERATORS, "GENERATORS")):
        for key, fn in getattr(module, declared, {}).items():
            _register(registry, key, fn, name)
    for rule in getattr(module, "COUNTS", ()):
        if rule not in COUNTS:
            COUNTS.append(rule)


def load():
    """Merge each parcel's declarations into the registries, for every parcel whose module is present (P0.1, after
    its verifier's round 1, D3: nothing registered a parcel's step for a real crate).

    A parcel's module, qro.register_<parcel>, declares what it registers, as STEPS {n: fn}, RAW_FORMS
    {name: fn}, COUNTS [fn] and GENERATORS {name: fn}. load() raises RegistrationError for:
      - a step whose refusals the vocabulary gives another parcel, or no parcel (step_owners);
      - a key another function holds, and a name of P0's fixture's, with --fixtures or without it;
      - a module that changes the registries while load() imports it, where it should declare;
      - any Exception a module raises while it is imported or its declarations are read, a Refused or a
        PermissionError among them (P0.1's verifier, round 2, R2-3: they gave exit 1, a verdict on a crate never
        read, and exit 2).
    The command line answers each as the checker itself failing, exit 3, as it does an exit or an interrupt raised
    at import: never a verdict. Loading twice changes nothing. A stated limit: a module that something imported
    before load() did, a parcel's own test say, has run already, so load() cannot see it change the registries.
    The command line's check and controls.run call load(); nothing else in process does."""
    owners = step_owners()
    for parcel in V.OWNERS:
        name = registration(parcel)
        if parcel == "P0" or (name not in sys.modules and importlib.util.find_spec(name) is None):
            continue
        try:
            before = _registries()
            module = importlib.import_module(name)
            if _registries() != before:
                raise RegistrationError(f"{name} changes the checker's registries itself; a parcel declares them")
            _declared(module, name, parcel, owners)
        except RegistrationError:
            raise
        except Exception as x:
            raise RegistrationError(f"{name} cannot be loaded: {describe(x)}") from x


def check(crate_dir):
    """The crate's metadata, if every step accepts it; otherwise Refused, at the first failure."""
    crate = Path(crate_dir)
    meta = crate / canonical.DESCRIPTOR
    if _is_link(meta):
        raise Refused("file-link", canonical.DESCRIPTOR, "the metadata file is a link: a crate holds files")
    if not meta.is_file() or canonical.DESCRIPTOR not in os.listdir(crate):     # its exact name, on every host
        raise Refused("file-missing", canonical.DESCRIPTOR, "the crate has no metadata file")
    md = reader.read(meta.read_bytes())
    files(crate, md)
    counts(crate, md)
    for n in range(4, 9):
        if STEPS[n] is not None:
            STEPS[n](crate, md)
            continue
        for e in md["@graph"]:
            for k in e:
                if k in V.TERM and V.TERM[k].step == n:
                    raise Refused("step-unbuilt", f"{e['@id']} {k}", f"step {n} is not built yet")
    regenerated(crate, md)
    return md


def _is_link(p):
    return p.is_symlink() or (hasattr(p, "is_junction") and p.is_junction())


def _unlistable(err):
    """A directory the walk cannot list is raised, never passed over: what the walk cannot see, it cannot check
    (P0's verifier, round 5, note 1). The command line answers it as misuse."""
    raise err


def walk(crate):
    """Every file in the crate, by its exact relative name; refusing any link, so that every path stays in it, and
    any other entry that is neither a regular file nor a directory, which no reader can hold to a digest. A
    directory it cannot list raises the host's error."""
    found = []
    for dirpath, dirnames, filenames in os.walk(crate, followlinks=False, onerror=_unlistable):
        dirnames.sort()                      # in place, so the walk descends in name order on every host
        for name in dirnames + sorted(filenames):
            p = Path(dirpath, name)
            rel = p.relative_to(crate).as_posix()
            if _is_link(p):
                raise Refused("file-link", rel, "a link in the crate: a crate holds files, never a way out of itself")
            if name in filenames and not p.is_file():
                raise Refused("file-link", rel, "neither a regular file nor a directory")
        found += [Path(dirpath, f).relative_to(crate).as_posix() for f in filenames]
    return set(found)


def files(crate, md):
    """Step 2."""
    on_disk = walk(crate)
    graph = {e["@id"]: e for e in md["@graph"]}
    local = {i: e for i, e in graph.items() if reader.local_file(e)}
    for i, e in sorted(local.items()):
        raw = "qro:RawResult" in canonical.types(e)
        if i not in on_disk:
            raise Refused("file-missing", i, "listed, and no file of that exact name is in the crate")
        if "sha256" not in e or "contentSize" not in e:
            raise Refused("raw-digest" if raw else "file-digest", i, "a file without its sha256 and contentSize")
        b = crate.joinpath(*i.split("/")).read_bytes()
        if hashlib.sha256(b).hexdigest() != e["sha256"] or str(len(b)) != e["contentSize"]:
            raise Refused("raw-digest" if raw else "file-digest", i, "the bytes are not the ones the metadata names")
    reached, todo = set(), [canonical.ROOT]
    while todo:
        e = graph.get(todo.pop())
        for ref in e.get("hasPart", []) if e is not None and isinstance(e.get("hasPart"), list) else []:
            if ref["@id"] not in reached:
                reached.add(ref["@id"])
                todo.append(ref["@id"])
    for i in sorted(local):
        if i not in reached:
            raise Refused("file-unlisted", i, "a file no hasPart reaches from the root")
    for rel in sorted(on_disk):
        if rel != canonical.DESCRIPTOR and rel not in local:
            raise Refused("file-unlisted", rel, "a file in the crate that no entity lists")


def counts(crate, md):
    """Step 3."""
    for e in md["@graph"]:                        # qro:shots stands only on a raw result: the reader holds its domain
        if "qro:RawResult" not in canonical.types(e):
            continue
        if not reader.local_file(e):
            raise Refused("graph-form", e["@id"], "a raw result is a File the crate holds")
        form = e.get("qro:rawForm")
        if form is None:
            raise Refused("raw-form", e["@id"], "a raw result that names no raw form")
        if form not in RAW_FORMS:
            raise Refused("step-unbuilt", f"{e['@id']} qro:rawForm", f"no reader is built for the raw form {form}")
        try:
            held = RAW_FORMS[form](crate.joinpath(*e["@id"].split("/")).read_bytes())
        except RawFormError as x:
            raise Refused("raw-form", e["@id"], f"not in the raw form {form}: {x}") from None
        except MemoryError:                           # the host's, never a verdict on the crate (FORMAT.md item 16)
            raise
        except Exception as x:                        # a reader that cannot read the bytes has refused them
            raise Refused("raw-form", e["@id"], f"the reader of {form} failed: {type(x).__name__}") from None
        if type(held) is not int or held < 0:
            raise Refused("raw-form", e["@id"], f"the reader of {form} counted no whole number of shots")
        if "qro:shots" in e and e["qro:shots"] != held:
            raise Refused("count-unpaid", f"{e['@id']} qro:shots", f"states {e['qro:shots']}; the bytes hold {held}")
    for rule in COUNTS:
        rule(crate, md)


def regenerated(crate, md):
    """Step 9."""
    root = md["@graph"][1]
    name = root["qro:generator"]
    if name not in GENERATORS:
        raise Refused("step-unbuilt", f"{canonical.ROOT} qro:generator", f"no generator {name} is built")
    try:
        want = canonical.dumps(canonical.body(GENERATORS[name](crate)))
    except MemoryError:                               # the host's, never a verdict on the crate (FORMAT.md item 16)
        raise
    except Exception as x:                            # a generator that cannot make the metadata is no match
        raise Refused("metadata-generated", f"{canonical.ROOT} qro:generator",
                      f"{name} failed on the records: {type(x).__name__}") from None
    have = canonical.dumps(canonical.body(md))
    if want != have:
        raise Refused("metadata-generated", canonical.first_difference(have, want) + " of the body",
                      f"not what {name} makes from the records")
