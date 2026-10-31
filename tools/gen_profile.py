#!/usr/bin/env python3
"""Generate the profile directory's files from the vocabulary table, and refuse drift (P4's design, items 1 and 8;
HonestFramework's templates/check_generated.py pattern, as tools/gen_vocabulary.py has it).

    python tools/gen_profile.py --write    # regenerate, after changing qro/vocabulary.py or qro/p4_examples.py
    python tools/gen_profile.py --check    # fail if a file is not exactly what the definitions render

The definitions are qro/vocabulary.py, which the shapes, the Profile Crate's DefinedTerms and the description are
rendered from, and qro/p4_examples.py, which the matrix of examples is. What is written, under profile/:
  - ro-crate-metadata.json, the Profile Crate (RO-Crate 1.3), and README.md, the description the profile's IRI
    resolves to, and EXAMPLES.md, the matrix of examples;
  - validator/qro-crate/, the shapes as SHACL Core Turtle in rocrate-validator's layout: profile.ttl, and a folder a
    requirement level (must/, should/); a folder with no shape is not written;
  - examples/fixture/, a copy of P0's fixture crate.
profile/context.jsonld is P0's: tools/gen_vocabulary.py writes it, and this tool reads its bytes and lists them in the
Profile Crate. So when the table changes both tools are run, and each fails its own --check until it is.

--check also holds the Profile Crate to the rules of RO-Crate 1.3's profiles page that its bytes show (qro/p4_profile.py,
check_profile_crate lists them; what it does not hold is stated as limits in profile/README.md), and lists a file under
profile/ that no definition renders and a directory that holds no file. The check reads any Profile Crate, however
misshapen, and refuses what it cannot read with a problem named: it is never why the tool answers 3. --write renders every
file, and holds the result to the same check, before it writes any; it removes a file under profile/ that no definition
renders, a link, and a directory that holds no file, P0's context aside.

Links. A link is a symbolic link or a directory junction, by the checker's own test (checker._is_link, FORMAT.md item 12): one
test, asked of every entry of every walk of this tool, on a host where os.walk(followlinks=False) still descends a junction.
A link is never descended, never read through, never written through and never removed through, and that holds for profile/
itself: a link there is refused in both modes, by a named problem and exit 1, before anything under it is read, walked, written
or removed. A link under profile/ is listed by --check, by its path, and --write removes the link itself and nothing behind it, as
it removes a stray file: profile/ is a crate, a crate holds files and never a way out of itself, and a refusal to write would
leave the tree stale until someone removed the link by hand, with nothing gained, since nothing behind a link is touched in
either choice. P0's context.jsonld is read through no link and removed by no one: a link or a directory there is refused,
by a named problem, as a missing file is.

What --write does with the rest of the tree, so that --check never advises what --write cannot do:
  - It writes each file beside its place and replaces it (os.replace), never through the place itself, so that another name of
    the old file, a hard link, keeps its bytes.
  - A name that differs only by case from a rendered name, or from P0's context.jsonld, is never removed or renamed: both modes
    refuse it by a named problem (exit 1), and --write removes and writes nothing while one is there.
  - It removes the strays first, then every directory that holds no file, and only then writes: a directory where a file goes is
    cleared once what it held is gone.
  - A directory the host cannot list is raised, never passed over (the checker's walk does the same): the tool fails, exit 3, and
    names the directory.
Stated limits. A file with the read-only attribute is neither removed nor replaced on Windows: --write fails on it, exit 3, and
names the files it had finished writing (where the directory, not the file, decides, it is replaced). An entry that is no
regular file, directory or link (a pipe or a device, on a host that has them) is read as a file would be. A junction whose
target is gone is a link only on a host that can open it, and the owner's machine cannot (found so on 2026-10-30, Windows 11,
Python 3.12: os.lstat of it raises FileNotFoundError, or NotADirectoryError where its target has become a file, so the checker's
test of a link finds none there, and removing the junction, tried by os.rmdir, os.unlink, shutil.rmtree, cmd's rmdir and a rename,
fails until its target is made again). With profile/ itself one, or with one at P0's context.jsonld, both modes refuse the tree,
exit 1, as one whose context is missing, for it is read and not listed; with any other below profile/, both fail, exit 3, naming a
directory the host cannot list; neither writes or removes anything. The tests make no such junction: they tell the tool that a link
stands at the path, as a host that opens one would answer. Where its stdout's reader is gone, Python itself ends the tool, exit
120, as gen_vocabulary.py's.
Exit 0: every file is exactly what its definitions render, and the Profile Crate holds the rules its check lists. 1: drift,
a file missing or unexpected, a link, a name that differs only by case, a directory that holds no file or stands where a file
goes, a Profile Crate that fails its check, or a profile/ that is a link, each with a diff or a reason. 2: the definitions
contradict themselves (the vocabulary's sanity check, a spelling with no shape constraint, a shape the model calls incoherent),
or the arguments are wrong. 3: the generator itself failed, with one line on stderr, escaped as the command line escapes its
own, which after --write names the files it had finished writing; this is never a verdict. No crash of the tool is exit 1,
the drift verdict's code and Python's for an uncaught exception: one in the arguments, in a module the tool imports or in the
tool is 3, and a failure to say a failure is no crash either. A name the output's code page cannot write is written as its
escape on the lines of every mode, never a crash; where a stream is closed the exit code still carries the verdict.
Stdlib only.
"""
import argparse
import difflib
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

try:
    from qro import canonical, checker  # noqa: E402
    from qro import p4_profile as P  # noqa: E402
    from qro import vocabulary as V  # noqa: E402
    from qro.__main__ import escape  # noqa: E402
except BaseException as _x:         # the tool could not start: exit 3, never Python's 1, the drift verdict's code
    if __name__ != "__main__":
        raise
    try:
        _text = f"{type(_x).__name__}: {_x}"
    except BaseException:
        _text = f"{type(_x).__name__}, whose text cannot be read"
    try:                            # qro is what failed, so its escape is not here: the line is escaped by ascii()
        sys.stderr.write("FAILED: the generator itself failed, " + ascii(_text)[1:-1] + "; this is not a verdict\n")
    except BaseException:
        pass                        # nowhere left to say it; the exit code still does
    sys.exit(3)

DIFF_LINES = 40         # a diff longer than this is cut: the file is regenerated whole, so the first lines say enough
TEMP = ".tmp"           # a file is written to its name and this, then replaces its place: no rendered path ends so
FIX = "  Fix by changing the definition and running --write; editing the file is never the fix.\n"
LINKED = ("profile/ is a link, and a link is never followed (FORMAT.md item 12): nothing under it is read, walked, written or "
          "removed, in either mode. Remove the link by hand and restore the directory.")
is_link = checker._is_link      # the checker's own test: a symbolic link or a directory junction, which Path.is_symlink misses


class Unlistable(RuntimeError):
    """A directory under profile/ that the host will not list."""


class Mute:
    """A stream that takes whatever is written to it and keeps none: what stands where the interpreter has no stream (a closed
    descriptor, pythonw). The verdict is the exit code, and it still says it."""
    def write(self, text):
        return len(text)

    def flush(self):
        pass


def problems():
    """The definitions' contradictions: the table's own (vocabulary.sanity, which holds the naming rule), then what
    stops it being rendered as shapes."""
    return V.sanity() + P.problems()


def unlistable(base):
    """os.walk's onerror for a walk of `base`: a directory the host will not list is raised, never passed over, since what the
    walk cannot see it can neither check nor clear. The checker's walk does the same (qro/checker.py, walk)."""
    def raise_it(err):
        try:
            rel = Path(err.filename).relative_to(base).as_posix()
        except (TypeError, ValueError):
            rel = str(err.filename)
        where = "" if rel == "." else rel + "/"
        raise Unlistable(f"profile/{where} is a directory the host cannot list ({type(err).__name__}), so nothing under it can "
                         "be checked or cleared") from err
    return raise_it


def walk(base):
    """(dirpath, directories, files, links) for `base` and each directory under it, top down. A link is never in the first
    two and never descended: os.walk(followlinks=False) leaves a symbolic link alone but descends a directory junction, which
    Path.is_symlink does not call a link, so the test is the checker's (is_link) and the walk is pruned by it. `links` are the
    entries of the directory, of either kind, for which it holds. A directory the host cannot list is raised (Unlistable)."""
    for dirpath, dirnames, filenames in os.walk(base, followlinks=False, onerror=unlistable(base)):
        links = sorted(name for name in dirnames + filenames if is_link(Path(dirpath, name)))
        dirnames[:] = [d for d in dirnames if d not in links]               # pruned in place: os.walk does not descend them
        yield dirpath, dirnames, [f for f in filenames if f not in links], links


def on_disk(root):
    """{path relative to profile/: bytes} for every file under it. A link is reported by its path with no bytes, and is never
    descended, read through or followed."""
    base = root / "profile"
    found = {}
    for dirpath, _, files, links in walk(base):
        for name in files:
            p = Path(dirpath, name)
            found[p.relative_to(base).as_posix()] = p.read_bytes()
        for name in links:
            found[Path(dirpath, name).relative_to(base).as_posix()] = b""
    return found


def empty_dirs(root):
    """The directories under profile/ that hold no file, however deep: git cannot commit one, a stale one is a leftover, and
    --write removes it. A link is not walked, and is an entry of on_disk()'s: a directory that holds only a link holds something,
    which --check lists by its path."""
    base = root / "profile"
    dirs, held = set(), set()
    for dirpath, _, files, links in walk(base):
        rel = Path(dirpath).relative_to(base).as_posix()
        if rel != ".":
            dirs.add(rel)
        held |= {(name if rel == "." else f"{rel}/{name}") for name in files + links}
    return sorted(d for d in dirs if not any(f.startswith(d + "/") for f in held))


def remove_empty_dirs(base):
    """Remove each directory under `base` that is empty now, deepest first, and `base` itself never. No link is walked, so
    nothing behind one is removed: a link is not a directory of `base`'s, whatever it points to."""
    for dirpath in reversed([d for d, _, _, _ in walk(base)]):
        if Path(dirpath) != base and not any(Path(dirpath).iterdir()):         # empty now, whatever walk listed before
            Path(dirpath).rmdir()


def remove_link(path):
    """Remove a link itself, and nothing behind it: unlink does it for a symbolic link and, measured on Windows, for a junction;
    rmdir is the fallback for a host that wants a directory link removed so. Never a path that is no link."""
    if not is_link(path):
        raise ValueError(f"{path} is no link, so it is not removed as one")
    try:
        path.unlink()
    except (IsADirectoryError, PermissionError):
        path.rmdir()


def replace_file(path, data):
    """Make `data` the whole of the file at `path` without writing through the place: to a new file beside it, which then
    replaces it (os.replace), so that another name of the old file, a hard link, keeps its bytes. A file this made and could not
    put in place is removed again, and a file it did not make never is."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + TEMP)
    made = False
    try:
        with open(tmp, "xb") as f:
            made = True
            f.write(data)
        os.replace(tmp, path)
    except BaseException:
        if made:
            try:
                tmp.unlink()
            except FileNotFoundError:
                pass
        raise


def fold(rel):
    """A path with case folded away: what two spellings of one name on a host that ignores case have in common."""
    return rel.casefold()


def case_clashes(rendered, have):
    """{path on disk: the spelling it should have} for each file or link under profile/ that is spelt otherwise than a rendered
    path or P0's context.jsonld, and equals one when case is folded. On a host that ignores case it is that file; on one that does
    not it is another name beside it. Either way it is never removed here, and --write refuses while one is there."""
    spelt = {fold(r): r for r in (*rendered, P.CONTEXT)}
    return {r: spelt[fold(r)] for r in sorted(have) if r not in rendered and r != P.CONTEXT and fold(r) in spelt}


def clash_problems(clashes):
    """[(path, what is wrong)] for `clashes`, one for each name that differs, as high up as the two spellings part: a directory
    spelt Validator holds files that are all clashes, and is said once."""
    parted = {}
    for have_rel, want_rel in clashes.items():
        have_parts, want_parts = have_rel.split("/"), want_rel.split("/")
        i = next(i for i, (a, b) in enumerate(zip(have_parts, want_parts)) if a != b)
        parted["/".join(have_parts[:i + 1])] = "/".join(want_parts[:i + 1])
    return [(path, "differs only by case from " + want + (", P0's file, which tools/gen_vocabulary.py writes" if want == P.CONTEXT
                                                            else ", which a definition renders")
             + "; it is never removed or renamed here, and --write refuses while it is there: rename or remove it by hand")
            for path, want in sorted(parted.items())]


def drift(root, rendered, have=None, clashes=None):
    """[(path, what is wrong)] for each file under profile/ that is not exactly what the definitions render, and each
    directory that holds no file. A name that differs only by case is a case_clashes() problem, and is not said again here."""
    out = []
    have = on_disk(root) if have is None else have
    clashes = case_clashes(rendered, have) if clashes is None else clashes
    for rel, want in sorted(rendered.items()):
        if rel in clashes.values():
            continue
        if rel not in have:
            if (root / "profile" / rel).is_dir():
                out.append((rel, "is a directory, not the file its definition renders; run --write removes it"))
            else:
                out.append((rel, "missing; run --write"))
        elif is_link(root / "profile" / rel):
            out.append((rel, "is a link, not the file its definition renders; run --write removes the link and writes the file"))
        elif have[rel] != want:
            lines = list(difflib.unified_diff(have[rel].decode("ascii", errors="replace").splitlines(True),
                                              want.decode("ascii", errors="replace").splitlines(True),
                                              "committed", "definition", n=1))
            cut = ["  " + ln if ln.endswith("\n") else "  " + ln + "\n" for ln in lines[:DIFF_LINES]]
            if len(lines) > DIFF_LINES:
                cut.append(f"  ... {len(lines) - DIFF_LINES} more lines\n")
            out.append((rel, "DRIFTED from its definition:\n" + "".join(cut)))
    for rel in sorted(set(have) - set(rendered) - {P.CONTEXT} - set(clashes)):
        if is_link(root / "profile" / rel):
            out.append((rel, "is a link, which no definition renders; run --write removes the link, and nothing behind it"))
        else:
            out.append((rel, "is rendered by no definition; run --write"))
    for rel in empty_dirs(root):
        out.append((rel + "/", "is a directory that holds no file; run --write"))
    return out


def crate_problems(root, files):
    """What RO-Crate 1.3's Profile Crate asks, held to `files` (the rendered set, or the one on disk) and P0's context."""
    return P.check_profile_crate(files, P.read_context(root))


def failed(x, writing, written):
    """The generator itself failed: one escaped line on stderr and exit 3, never a verdict. Where the line cannot be written, the
    exit code still says it, and the failure to say it is no crash."""
    after = f"it had finished writing {', '.join(written) or 'no file'}" if writing else "this is not a verdict"
    try:
        sys.stderr.write(escape(f"FAILED: the generator itself failed, {checker.describe(x)}; {after}") + "\n")
    except BaseException:
        pass
    return 3


def main(argv=None, root=ROOT):
    try:
        ap = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else None)   # python -OO strips the docstring
        g = ap.add_mutually_exclusive_group(required=True)
        g.add_argument("--write", action="store_true")
        g.add_argument("--check", action="store_true")
        args = ap.parse_args(argv)
    except SystemExit:
        raise                       # argparse's own, and nothing else's: 2 for the arguments, 0 for --help
    except BaseException as x:      # a crash before the work: exit 3, not the exit 1 of an uncaught exception
        return failed(x, False, [])
    written = []
    try:
        return _run(args, Path(root), written)
    except BaseException as x:      # the generator itself failed: never a verdict (P0.2's verifier, as gen_vocabulary)
        return failed(x, args.write, written)


def _run(args, root, written):
    if is_link(root / "profile"):                   # first: before anything under it is read, walked, written or removed
        sys.stderr.write(escape(LINKED) + "\n")
        return 1
    found = problems()
    if found:
        sys.stderr.write("the definitions contradict themselves:\n" + "".join(f"  {escape(p)}\n" for p in found))
        return 2
    try:
        rendered = P.render(root)
    except P.ContextMissing as x:
        sys.stderr.write(escape(str(x)) + "\n")
        return 1
    if args.write:
        bad = crate_problems(root, rendered)
        if bad:
            sys.stderr.write("the Profile Crate would not hold the rules of RO-Crate 1.3's profiles page that its check lists, "
                             "so nothing is written:\n"
                             + "".join(f"  {escape(p)}\n" for p in bad))
            return 1
        base = root / "profile"
        have = on_disk(root)
        stuck = clash_problems(case_clashes(rendered, have))
        if stuck:
            sys.stderr.write("a name clashes by case with a rendered one, so nothing is written or removed:\n"
                             + "".join(f"  profile/{escape(path)} {what}\n" for path, what in stuck))
            return 1
        for rel in sorted(r for r in have if r != P.CONTEXT and (r not in rendered or is_link(base / r))):
            (remove_link if is_link(base / rel) else Path.unlink)(base / rel)       # a link at a path to write goes too: no write through it
            written.append(f"removed {rel}")
            print(f"removed {rel}", flush=True)
        remove_empty_dirs(base)                     # before the writes: a directory where a file goes holds only what was removed
        for rel, data in sorted(rendered.items()):
            replace_file(base / rel, data)
            written.append(rel)
            print(f"wrote {rel}", flush=True)
        return 0
    have = on_disk(root)
    clashes = case_clashes(rendered, have)
    stuck = clash_problems(clashes)
    for path, what in stuck:
        sys.stderr.write(f"profile/{escape(path)} {what}\n")
    bad = drift(root, rendered, have, clashes)
    for rel, what in bad:
        sys.stderr.write(f"profile/{rel} {what}")
        sys.stderr.write(FIX)
    missing_crate = canonical.DESCRIPTOR not in have
    problems_found = [] if missing_crate else crate_problems(root, have)
    for p in problems_found:
        sys.stderr.write(f"profile/{canonical.DESCRIPTOR} {escape(p)}\n")
    named = {b for b, _ in bad} | set(clashes.values())
    for rel in rendered:
        if rel not in named:
            print(f"profile/{rel} is exactly what its definition renders")
    return 1 if stuck or bad or problems_found else 0


if __name__ == "__main__":
    # a name the output's code page cannot write is written as its escape, never a crash (P4's third verifier, note 4, MEASURED:
    # a stray file named in CJK characters, stdout redirected in cp1252, exit 3 after --write had removed it and before it
    # wrote anything). Where a stream cannot be reconfigured (a stream with no reconfigure; one whose reconfigure raises) it is
    # left as it is, as P0.6's gate leaves it; where there is none (None, under pythonw or a closed descriptor) a mute one stands in,
    # so that a line that cannot be said is no crash and the exit code still carries the verdict.
    for name in ("stdout", "stderr"):
        stream = getattr(sys, name)
        if stream is None:
            setattr(sys, name, Mute())
            continue
        try:
            stream.reconfigure(errors="backslashreplace")
        except Exception:
            pass
    sys.exit(main())
