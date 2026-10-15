#!/usr/bin/env python3
"""The documents' own gate: the mistakes a documentation set can make, refused. Copied from moth-quantum's
tools/check_docs.py at 3a73823 (study QRO-0, section 13's floor). QRO-Crate's changes (P0's verifier, rounds 2 to
5, and P0.1): its directories and its root documents; the repositories whose paths it leaves alone (FOREIGN), and
the paths the runner guards with `need_file`; a missing index
is itself a problem; links are checked in every markdown file under docs/ and records/, not only in the documents;
a link's document is named with forward slashes; the summary counts the other markdown files and the source files,
and says every path named exists; and this docstring, rewritten for them, drops two sentences of moth-quantum's (a
link's breaking as "the cheapest possible own goal", and the history of its tests' move), and says "directly under
docs/" and what of docs/studies/ it leaves alone.

  1. Every relative markdown link resolves to a file or directory that exists: in the documents, and in every
     other markdown file under docs/ and records/, the study's and the verifiers' reports among them.
  2. docs/README.md, the index, links every document directly under docs/. An unindexed document is one nobody
     finds.
  3. Every repository path named in plain text exists: in the documents, and in the package's, the controls',
     the tools', the tests' and the runner's own text. Not checked: a path marked "(new)", which a plan names
     before it exists; a path the runner guards with `need_file`, and anything under it, while the path is
     missing and the runner skips its stage by name (P0.1: the parcels' stages, written before the parcels
     build); a line that
     names another repository (moth-quantum, cft-fp256, ...), whose paths are that repository's; tests/docs/,
     whose tests plant missing paths on purpose; and the study under docs/studies/, which has its own gate and
     cites moth-quantum's paths on lines that do not name it.

    python tools/check_docs.py      # 0 = clean; 1 = each problem printed by name
"""
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
LINK = re.compile(r"\[[^\]]*\]\(([^)#\s]+)(?:#[^)]*)?\)")
PATH = re.compile(r"(?<![\w./-])((?:tests|qro|controls|tools|docs|verify|profile|records)/[\w./-]*\w)")
FOREIGN = ("moth-quantum", "quantum_film", "Quantum-Film", "atlas-film", "cft-fp256", "HonestFramework",
           "ParcelRound", "HonestHarness")


def documents(root=ROOT):
    return ([root / n for n in ("README.md", "CLAUDE.md", "LICENSE-docs.md", "NOTICE.md") if (root / n).exists()]
            + sorted((root / "docs").glob("*.md")))


def link_checked(root=ROOT):
    """Every markdown file whose links are checked: the documents, and every other under docs/ and records/ (P0's
    verifier, round 3, note 14: the study's and the reports' links were checked by no gate)."""
    more = {p for d in ("docs", "records") if (root / d).exists() for p in (root / d).rglob("*.md")}
    return documents(root) + sorted(more - set(documents(root)))


def problems(root=ROOT):
    out = []
    for doc in link_checked(root):
        for target in LINK.findall(doc.read_text(encoding="utf-8")):
            if "://" in target or target.startswith("mailto:"):
                continue
            if not (doc.parent / target).resolve().exists():
                out.append(f"{doc.relative_to(root).as_posix()}: link to {target} does not resolve")
    index = root / "docs" / "README.md"
    if index.exists():
        linked = {(index.parent / t).resolve() for t in LINK.findall(index.read_text(encoding="utf-8"))}
        for doc in sorted((root / "docs").glob("*.md")):
            if doc != index and doc.resolve() not in linked:
                out.append(f"docs/README.md does not index {doc.name}")
    else:
        out.append("docs/README.md, the index, is missing")
    return out + missing_paths(root)


def texts(root=ROOT):
    """The documents, and the text of the package, the controls, the tools, the tests and the runner."""
    out = documents(root)
    for d in ("qro", "controls", "tools", "tests", "verify"):
        out += sorted(p for p in (root / d).rglob("*") if p.suffix in (".py", ".sh"))
    return out


def guarded(root=ROOT):
    """The paths the runner guards with `need_file` that are missing, so that it skips their stages by name. Once a
    path exists its exemption ends, and every path named below it is checked again (P0.1's verifier, round 2,
    R2-2: the exemption had no end)."""
    runner = root / "verify" / "run.sh"
    text = runner.read_text(encoding="utf-8") if runner.exists() else ""
    return {g for g in re.findall(r"^need_file ([\w./-]+) ", text, re.M) if not (root / g).exists()}


def missing_paths(root=ROOT):
    out, skipped = [], guarded(root)
    for f in texts(root):
        rel = f.relative_to(root).as_posix()
        if rel.startswith("tests/docs/"):
            continue
        for n, line in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
            if any(name in line for name in FOREIGN):
                continue
            for m in PATH.finditer(line):
                planned = line[m.end():].lstrip("/`'\" ").startswith("(new)") or any(
                    m.group(1) == g or m.group(1).startswith(g + "/") for g in skipped)
                if not planned and not (root / m.group(1)).exists():
                    out.append(f"{rel}:{n}: names {m.group(1)}, which does not exist")
    return out


if __name__ == "__main__":
    found = problems()
    for p in found:
        print(p)
    if not found:
        print(f"{len(documents())} documents, {len(link_checked()) - len(documents())} other markdown files and "
              f"{len(texts()) - len(documents())} source files: every relative link resolves, the index lists every "
              "document, and every path named exists, but for those item 3 leaves unchecked")
    sys.exit(1 if found else 0)
