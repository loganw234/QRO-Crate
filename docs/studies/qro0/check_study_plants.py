"""A test of check_study.py. It plants faults in LF copies of study QRO-0 and in copies of docs/studies/qro0/, in a
temporary directory, and runs the gate on each copy, with a time limit of 120 seconds a run. Stdlib only; Python 3.11
or later. It writes nothing outside that directory, which it removes.

It refuses unless every plant is placed, every fault is refused with the failure it targets, and every right variant
is accepted. Each fault names a piece of the failure line it expects, so a refusal for another reason does not count.
It prints each plant's result, then the counts. A plant is placed when the text it changes is found. The study's
wording moves on, so a plant that cannot be placed is a failure, not a pass.

The faults follow the gate's four checks:
  1. draft numbers (18): each of the six sentences made stale; the header's "answers" sentence, sections 13's and
     15's sentences and section 17's "changed" label each moved out of its own place; a stale copy beside a right
     one, for both header sentences and in sections 13 and 15; a stale copy of section 13's sentence in the header,
     of section 15's in section 13, and of the header's "re-check" sentence in section 15; a header line without its
     full stop;
  2. tables (12): a short row in an indented table, and after a spaced delimiter; a short delimiter; two hyphens in a
     delimiter's first cell, and in a later one; letters in a delimiter cell; a blank line and a prose line inside a
     table; a pipe-led line above a header, and one alone; a row without its trailing pipe, with and without a cell
     more;
  3. section references (17): a section that is not a heading, cited capitalised, in capitals, wrapped, mid-list,
     after a serial comma, at a range's end, after "or", a slash, a hyphen and an en dash, and as a subsection; in
     section 17's "where" cells, in a first and a last row, after "and" and after ", and"; after ".md," and ".md;",
     which the skip does not cover;
  4. instruments (21): a first hash written with "...", a row with a trailing space, a row holding a character the
     console cannot print; a deleted and a duplicated row, a tool with no row, a hyphenated tool, a row for a missing
     tool; the right output hash written five ways the row does not parse, and an output cell with extra text; a
     wrong output hash in the right form; an unlisted file, a subdirectory; a changed byte in a tool, in an output and
     in the gate, and a missing output.
The right variants (6): the draft itself; section 13's sentence wrapped across lines; older drafts' labels in section
17; a table with a spaced delimiter; a reference to a section that is not a heading, just after a ".md" name; a
"where" cell outside section 17 citing one.

Usage: python -I check_study_plants.py <path to QRO-0.md>
"""
import locale
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

if __name__ != "__main__":
    raise ImportError("a test, not a module")
sys.stdout.reconfigure(errors="backslashreplace")

STUDY = Path(sys.argv[1]).resolve()
QRO0 = STUDY.parent / "qro0"
BASE = STUDY.read_bytes().decode("utf-8").replace("\r\n", "\n")
UNESC = re.compile(r"(?<!\\)\|")                                 # an unescaped pipe


class Unplaced(Exception):
    pass


def need(items, what):
    for item in items:
        return item
    raise Unplaced(f"no {what}")


HEADER = re.search(r"\*\*Draft (\d+), (\d{4}-\d{2}-\d{2})\.\*\*", BASE)
N = int(HEADER.group(1)) if HEADER else 0
HEADINGS = set(re.findall(r"^#{2,3} (\d+(?:\.\d+)?)\.? ", BASE, re.M))
TOP = sorted(int(h) for h in HEADINGS if "." not in h) or [0, 1, 2]
BAD, GOOD1, GOOD2 = TOP[-1] + 1, TOP[1], TOP[2]              # BAD is no heading; GOOD1 and GOOD2 are


def once(pattern, new, text=None):
    """Replace the one match of a regex pattern with `new`, a string or a function of the match."""
    t = BASE if text is None else text
    found = list(re.finditer(pattern, t, re.M))
    if len(found) != 1:
        raise Unplaced(f"{len(found)} matches for {pattern[:60]!r}")
    m = found[0]
    return t[:m.start()] + (new(m) if callable(new) else new) + t[m.end():]


def before(heading, insert, text=None):
    """Insert a paragraph just before a top-level heading, such as 13 or "Contents"."""
    return once(rf"^(?=## {heading}(?:\. |\s*$))", insert + "\n\n", text)


def tables(text):
    """Each table as (index of its header line, number of lines), found as the gate finds them."""
    ls, out, i = text.split("\n"), [], 0
    while i < len(ls):
        if not ls[i].strip().startswith("|"):
            i += 1
            continue
        j = i
        while j < len(ls) and ls[j].strip().startswith("|"):
            j += 1
        if j - i >= 2 and re.match(r"^\|\s*:?-{3,}", ls[i + 1].strip()):
            out.append((i, j - i))
        i = j
    return out


def edit_lines(fn):
    ls = BASE.split("\n")
    fn(ls)
    return "\n".join(ls)


def drop_last_cell(line):
    r = line.rstrip()
    return r[:r.rfind("|", 0, len(r) - 1) + 1]


def plain():
    """The first table that is not indented, has three or more columns and two or more body rows, and no backslash."""
    ls = BASE.split("\n")
    return need((h for h, n in tables(BASE) if not ls[h].startswith(" ") and n >= 4 and "\\" not in ls[h]
                 and len(UNESC.split(ls[h].strip())) >= 5), "plain table")


def on_plain(fn):
    h = plain()
    return edit_lines(lambda ls: fn(ls, h))


def indented_short_row(ls):
    h = need((h for h, n in tables(BASE) if BASE.split("\n")[h].startswith(" ") and n >= 3), "indented table")
    ls[h + 2] = drop_last_cell(ls[h + 2])


def spaced(ls, h, short):
    indent = ls[h + 1][:len(ls[h + 1]) - len(ls[h + 1].lstrip())]
    ls[h + 1] = indent + "| " + " | ".join(["---"] * (len(UNESC.split(ls[h].strip())) - 2)) + " |"
    if short:
        ls[h + 2] = drop_last_cell(ls[h + 2])


def delimiter_cell(ls, h, k, value):
    parts = ls[h + 1].split("|")
    parts[k] = value
    ls[h + 1] = "|".join(parts)


def where_edit(row, suffix, in_s17=True):
    """Append to the "where" cell of the first or last row of the first table with a "where" column."""
    def fn(ls):
        s17 = need((i for i, line in enumerate(ls) if line.startswith("## 17. ")), "section 17")
        found = []
        for h, n in tables("\n".join(ls)):
            if (h > s17) == in_s17:
                head = [c.strip().lower() for c in UNESC.split(ls[h].strip())[1:-1]]
                if "where" in head:
                    found.append((h, n, head.index("where")))
        h, n, w = need(found, "table with a where column")
        k = h + 2 if row == "first" else h + n - 1
        parts = UNESC.split(ls[k])
        parts[w + 1] = parts[w + 1].rstrip() + suffix + " "
        ls[k] = "|".join(parts)
    return lambda: edit_lines(fn)


ROW = re.compile(r"^\| `([A-Za-z0-9_]+\.py)` \| `([0-9a-f]{8})…`[^|]*\| ([^|]*) \| ([^|]*) \|$", re.M)


def out_row():
    return need((m for m in ROW.finditer(BASE) if ".out.txt" in m.group(3)), "row with an output")


def tool():
    return out_row().group(1)


def output():
    return out_row().group(3).strip().strip("`")


def row_with(first=None, cell3=None, cell4=None, extra=None):
    m = out_row()
    r = m.group(0)
    if first is not None:
        r = r.replace(f"`{m.group(2)}…`", first, 1)
    if cell3 is not None:
        r = r.replace(f"| {m.group(3)} |", f"| {cell3} |", 1)
    if cell4 is not None:
        r = r[:r.rstrip("|").rstrip().rfind("|") + 1] + f" {cell4} |"
    if extra is not None:
        r = extra(r)
    return BASE.replace(m.group(0), r, 1)


def right_hash():
    return re.search(r"[0-9a-f]{8}", out_row().group(4)).group(0)


def flip(path):
    b = bytearray(path.read_bytes())
    b[-1] ^= 1
    path.write_bytes(bytes(b))


def gate_docstring(q):
    g = q / "check_study.py"
    b = g.read_bytes()
    if b.count(b"A gate on study") != 1:
        raise Unplaced("the gate's docstring has moved")
    g.write_bytes(b.replace(b"A gate on study", b"A gate on studY"))


S13 = rf"Drafts\s+1\s+to\s+{N - 1}\s+went\s+past\s+verifiers,\s+and\s+draft\s+{N}\s+goes\s+next"
S15 = rf"the\s+re-checks\s+of\s+drafts\s+2\s+to\s+{N - 1}\b"
W13 = f"Drafts 1 to {N - 1} went past verifiers, and draft {N} goes next"
W15 = f"the re-checks of drafts 2 to {N - 1}"
OLD13 = f"Drafts 1 to {N - 2} went past verifiers, and draft {N - 1} goes next"
OLD15 = f"the re-checks of drafts 2 to {N - 2}"
STALE = "the header or section 13 or 15: a stale"

PLANTS = [
    # 1. draft numbers (18)
    ("refuse", "header 'answers' stale", f"the header: no '**Draft {N}** answers'",
     lambda: once(rf"\*\*Draft {N}\*\* answers", f"**Draft {N - 1}** answers"), None),
    ("refuse", "header 're-check' stale", f"the header: no 'a re-check of draft {N}'s changes'",
     lambda: once(rf"a re-check of draft {N}'s changes", f"a re-check of draft {N - 1}'s changes"), None),
    ("refuse", "section 13 stale", f"section 13: no '{W13}'", lambda: once(S13, OLD13), None),
    ("refuse", "section 15 stale", f"section 15: no '{W15}'", lambda: once(S15, OLD15), None),
    ("refuse", "section 17 'changed' stale", f"section 17: no 'what draft {N} changed'",
     lambda: once(rf"what draft {N} changed", f"what draft {N - 1} changed"), None),
    ("refuse", "section 17 'instruments' stale", f"section 17: no 'The instruments, in draft {N}'",
     lambda: once(rf"The instruments, in draft {N}\b", f"The instruments, in draft {N - 1}"), None),
    ("refuse", "header 'answers' moved to section 0", f"the header: no '**Draft {N}** answers'",
     lambda: before(1, f"**Draft {N}** answers it.", once(rf"\*\*Draft {N}\*\* answers", f"Draft {N} answers")), None),
    ("refuse", "section 13's sentence moved to 12", f"section 13: no '{W13}'",
     lambda: before(13, W13 + ".", once(S13, "The drafts went past their verifiers")), None),
    ("refuse", "section 15's sentence moved to 14", f"section 15: no '{W15}'",
     lambda: before(15, "Quoted: " + W15 + ".", once(S15, "the earlier re-checks")), None),
    ("refuse", "section 17 'changed' moved to 16", f"section 17: no 'what draft {N} changed'",
     lambda: before(17, f"what draft {N} changed.", once(rf"what draft {N} changed", f"what draft {N} altered")), None),
    ("refuse", "header 'answers' stale copy", f"{STALE} '**Draft {N - 1}** answers'",
     lambda: before("Contents", f"- **Draft {N - 1}** answers nothing."), None),
    ("refuse", "header 're-check' stale copy", f"{STALE} 'a re-check of draft {N - 1}'s changes'",
     lambda: before("Contents", f"- and a re-check of draft {N - 1}'s changes."), None),
    ("refuse", "section 13 stale copy", f"{STALE} '{OLD13}'", lambda: once(S13, lambda m: m.group(0) + ". " + OLD13), None),
    ("refuse", "section 15 stale copy", f"{STALE} '{OLD15}'", lambda: before(16, f"Also {OLD15}."), None),
    ("refuse", "section 13's sentence, stale, in the header", f"{STALE} '{OLD13}'",
     lambda: before("Contents", OLD13 + "."), None),
    ("refuse", "section 15's sentence, stale, in section 13", f"{STALE} '{OLD15}'",
     lambda: before(14, f"Also {OLD15}."), None),
    ("refuse", "the header's 're-check', stale, in section 15", f"{STALE} 'a re-check of draft {N - 1}'s changes'",
     lambda: before(16, f"Also a re-check of draft {N - 1}'s changes."), None),
    ("refuse", "header line without its full stop", "header: no 'Draft N, YYYY-MM-DD.' line",
     lambda: once(rf"\*\*Draft {N}, (\d{{4}}-\d{{2}}-\d{{2}})\.\*\*", lambda m: f"**Draft {N}, {m.group(1)}**"), None),
    # 2. tables (12)
    ("refuse", "indented table, short row", "a table row with", lambda: edit_lines(indented_short_row), None),
    ("refuse", "spaced delimiter, short row", "a table row with", lambda: on_plain(lambda ls, h: spaced(ls, h, True)), None),
    ("refuse", "short delimiter", "a table row with",
     lambda: on_plain(lambda ls, h: ls.__setitem__(h + 1, drop_last_cell(ls[h + 1]))), None),
    ("refuse", "two hyphens, first delimiter cell", "in no table",
     lambda: on_plain(lambda ls, h: delimiter_cell(ls, h, 1, "--")), None),
    ("refuse", "two hyphens, later delimiter cell", "a delimiter cell '--'",
     lambda: on_plain(lambda ls, h: delimiter_cell(ls, h, 2, "--")), None),
    ("refuse", "letters in a delimiter cell", "a delimiter cell 'abc'",
     lambda: on_plain(lambda ls, h: delimiter_cell(ls, h, 2, "abc")), None),
    ("refuse", "blank line inside a table", "in no table", lambda: on_plain(lambda ls, h: ls.insert(h + 3, "")), None),
    ("refuse", "prose line inside a table", "in no table",
     lambda: on_plain(lambda ls, h: ls.insert(h + 3, "a line of prose")), None),
    ("refuse", "pipe-led line above a header", "in no table", lambda: on_plain(lambda ls, h: ls.insert(h, "| stray |")), None),
    ("refuse", "pipe-led line alone", "in no table", lambda: before(16, "| stray |"), None),
    ("refuse", "row without its trailing pipe", "does not start and end",
     lambda: on_plain(lambda ls, h: ls.__setitem__(h + 2, ls[h + 2].rstrip()[:-1])), None),
    ("refuse", "row without its trailing pipe, a cell more", "does not start and end",
     lambda: on_plain(lambda ls, h: ls.__setitem__(h + 2, ls[h + 2].rstrip()[:-1] + "| extra")), None),
    # 3. section references (17)
    ("refuse", "capitalised", f"section {BAD} is not a heading", lambda: before(16, f"See Section {BAD}."), None),
    ("refuse", "in capitals", f"section {BAD} is not a heading", lambda: before(16, f"See SECTION {BAD}."), None),
    ("refuse", "wrapped", f"section {BAD} is not a heading", lambda: before(16, f"See section\n{BAD} here."), None),
    ("refuse", "mid-list", f"section {BAD} is not a heading",
     lambda: before(16, f"See sections {GOOD1}, {BAD} and {GOOD2}."), None),
    ("refuse", "after a serial comma", f"section {BAD} is not a heading",
     lambda: before(16, f"See sections {GOOD1}, {GOOD2}, and {BAD}."), None),
    ("refuse", "at a range's end", f"section {BAD} is not a heading", lambda: before(16, f"See sections {GOOD1} to {BAD}."), None),
    ("refuse", "after 'or'", f"section {BAD} is not a heading", lambda: before(16, f"See sections {GOOD1} or {BAD}."), None),
    ("refuse", "after a slash", f"section {BAD} is not a heading", lambda: before(16, f"See sections {GOOD1}/{BAD}."), None),
    ("refuse", "after a hyphen", f"section {BAD} is not a heading", lambda: before(16, f"See sections {GOOD1}-{BAD}."), None),
    ("refuse", "after an en dash", f"section {BAD} is not a heading",
     lambda: before(16, f"See sections {GOOD1}–{BAD}."), None),
    ("refuse", "a subsection", f"section {TOP[-1]}.99 is not a heading", lambda: before(16, f"See section {TOP[-1]}.99."), None),
    ("refuse", "a 'where' cell, first row", f"cites section {BAD}", where_edit("first", f", {BAD}"), None),
    ("refuse", "a 'where' cell, last row", f"cites section {BAD}", where_edit("last", f", {BAD}"), None),
    ("refuse", "a 'where' cell, after 'and'", f"cites section {BAD}", where_edit("first", f" and {BAD}"), None),
    ("refuse", "a 'where' cell, after ', and'", f"cites section {BAD}", where_edit("first", f", {GOOD1}, and {BAD}"), None),
    ("refuse", "after '.md,' and more words", f"section {BAD} is not a heading",
     lambda: before(16, f"See METHOD.md, and see section {BAD}."), None),
    ("refuse", "after '.md;'", f"section {BAD} is not a heading", lambda: before(16, f"See METHOD.md; section {BAD}."), None),
    # 4. instruments (21)
    ("refuse", "first hash with '...'", "a row does not parse", lambda: row_with(first=f"`{out_row().group(2)}...`"), None),
    ("refuse", "row with a trailing space", "a row does not parse", lambda: row_with(extra=lambda r: r + " "), None),
    ("refuse", "row with an unprintable character", "a row does not parse",
     lambda: row_with(first=f"− `{out_row().group(2)}…`"), None),
    ("refuse", "row deleted", "but has no row", lambda: BASE.replace(out_row().group(0) + "\n", "", 1), None),
    ("refuse", "row duplicated", "has 2 rows",
     lambda: BASE.replace(out_row().group(0), out_row().group(0) + "\n" + out_row().group(0), 1), None),
    ("refuse", "tool with no row", "extra_tool.py is in qro0/ but has no row", None,
     lambda q: (q / "extra_tool.py").write_text("print(1)\n")),
    ("refuse", "hyphenated tool", "my-tool.py is in qro0/ but has no row", None,
     lambda q: (q / "my-tool.py").write_text("print(1)\n")),
    ("refuse", "row for a missing tool", "which is not in qro0/", None, lambda q: (q / tool()).unlink()),
    ("refuse", "right output hash with '...'", "output or hash cell does not parse",
     lambda: row_with(cell4=f"`{right_hash()}...`"), None),
    ("refuse", "right output hash, no ellipsis", "output or hash cell does not parse",
     lambda: row_with(cell4=f"`{right_hash()}`"), None),
    ("refuse", "right output hash in capitals", "output or hash cell does not parse",
     lambda: row_with(cell4=f"`{right_hash().upper()}…`"), None),
    ("refuse", "right output hash, no backticks", "output or hash cell does not parse",
     lambda: row_with(cell4=f"{right_hash()}…"), None),
    ("refuse", "right output hash with a suffix", "output or hash cell does not parse",
     lambda: row_with(cell4=f"`{right_hash()}…` (CRLF)"), None),
    ("refuse", "output cell with extra text", "output or hash cell does not parse",
     lambda: row_with(cell3=f"`{output()}` (CRLF)"), None),
    ("refuse", "wrong output hash, right form", "the table says deadbeef", lambda: row_with(cell4="`deadbeef…`"), None),
    ("refuse", "unlisted file", "notes.txt: a file no row names", None, lambda q: (q / "notes.txt").write_text("notes\n")),
    ("refuse", "subdirectory", "sub/: a directory", None,
     lambda q: ((q / "sub").mkdir(), (q / "sub" / "extra.py").write_text("print(1)\n"))),
    ("refuse", "tool byte changed", "hashes", None, lambda q: flip(q / tool())),
    ("refuse", "output byte changed", "hashes", None, lambda q: flip(q / output())),
    ("refuse", "output missing", "hashes missing", None, lambda q: (q / output()).unlink()),
    ("refuse", "gate byte changed", "check_study.py hashes", None, gate_docstring),
    # right variants (6)
    ("accept", "the draft itself", None, lambda: BASE, None),
    ("accept", "section 13's sentence wrapped", None,
     lambda: once(S13, lambda m: re.sub(r"\s+", " ", m.group(0)).replace(" verifiers,", "\nverifiers,")), None),
    ("accept", "older drafts' labels in section 17", None,
     lambda: BASE + "\nwhat draft 3 changed. The instruments, in draft 2.\n", None),
    ("accept", "a table with a spaced delimiter", None, lambda: on_plain(lambda ls, h: spaced(ls, h, False)), None),
    ("accept", "a reference just after a '.md' name", None, lambda: before(16, f"See METHOD.md section {BAD}."), None),
    ("accept", "a 'where' cell outside section 17", None, where_edit("first", f", {BAD}", in_s17=False), None),
]

counts = {"refused": 0, "accepted": 0, "wrong": 0, "unplaced": 0}
with tempfile.TemporaryDirectory() as tmp:
    for k, (expect, name, want, make_text, edit_qro0) in enumerate(PLANTS):
        d = Path(tmp) / f"p{k:02d}"
        try:
            if not HEADER:
                raise Unplaced("the study has no 'Draft N, YYYY-MM-DD.' line")
            text = make_text() if make_text else BASE
            shutil.copytree(QRO0, d / "qro0")
            (d / "QRO-0.md").write_bytes(text.encode("utf-8"))
            if edit_qro0:
                edit_qro0(d / "qro0")
        except (Unplaced, IndexError, ValueError, OSError) as e:
            counts["unplaced"] += 1
            print(f"UNPLACED  {name}: {e}")
            continue
        try:
            r = subprocess.run([sys.executable, "-I", str(d / "qro0" / "check_study.py"), str(d / "QRO-0.md")],
                               capture_output=True, timeout=120)
        except subprocess.TimeoutExpired:
            counts["wrong"] += 1
            print(f"WRONG     {name}: the gate ran past 120 s")
            continue
        out = r.stdout.decode(locale.getencoding(), errors="replace").splitlines()
        named = [line for line in out if line.startswith("REFUSED: ")]
        if expect == "refuse" and r.returncode == 1 and any(want in line for line in named):
            counts["refused"] += 1
            print(f"refused   {name}: {next(line for line in named if want in line)[9:]}"
                  + (f" (+{len(named) - 1})" if len(named) > 1 else ""))
        elif expect == "accept" and r.returncode == 0 and out[-1:] == ["ACCEPTED"]:
            counts["accepted"] += 1
            print(f"accepted  {name}")
        else:
            counts["wrong"] += 1
            print(f"WRONG     {name}: expected to {expect}" + (f" with '{want}'" if want else "")
                  + f", exit {r.returncode}: {' / '.join(out)[:240]}")

print(f"{counts['refused']} faults refused with the failure each targets, {counts['accepted']} right variants "
      f"accepted, {counts['unplaced']} unplaced, {counts['wrong']} wrong")
if counts["wrong"] or counts["unplaced"]:
    print("REFUSED")
    sys.exit(1)
print("ACCEPTED")
