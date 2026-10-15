"""A gate on study QRO-0's own text, for the slips its verifiers kept finding by hand. Stdlib only, read-only.

It refuses, naming each failure, unless all four of these hold.
  1. Draft numbers. The header's draft number N agrees with six sentences, each found in its own place:
       - the header's "**Draft N** answers" and "a re-check of draft N's changes";
       - section 13's "Drafts 1 to N-1 went past verifiers, and draft N goes next";
       - section 15's "the re-checks of drafts 2 to N-1";
       - section 17's "what draft N changed" and "The instruments, in draft N".
     Across the header and sections 13 and 15, every copy of the first four, in this wording, must name N, in
     whichever of the three it stands. Section 17 keeps each draft's labels, so there N's need only be present.
  2. Tables. Every line that starts with a pipe, after any indent, belongs to a table: a run of such lines whose
     second line is a delimiter row. In each table, every row starts and ends with an unescaped pipe and has as many
     cells as the header row, and every delimiter cell is three or more hyphens, with optional colons.
  3. Section references. Every section number it reads names one of the study's headings. It reads them
       - after "section" or "sections", in any case and across line breaks: a number alone, or a list or range
         joined by commas, "and", "or", "to", a slash, a hyphen or an en dash;
       - as bare numbers in the "where" column of section 17's tables, between commas, "and" or ", and".
     It skips a reference just after a file name ending ".md", such as "METHOD.md section 7", as another
     document's.
  4. Instruments. Section 15 has exactly one row for each .py file in docs/studies/qro0/, none for any other .py
     file, and each row parses.
     Each row names the SHA-256 prefix of its file. A row whose output cell names a .out.txt file names it alone,
     and that file's prefix in the next cell. docs/studies/qro0/ holds nothing but those .py and .out.txt files.

It checks nothing else. Among what that leaves unchecked:
  - prose and figures. It re-runs no instrument, so a matching output hash shows only that the file is unchanged;
  - the header's date;
  - draft numbers outside those six sentences, including a stale copy of one in other wording, or outside the
    header and sections 13 and 15, such as a quotation in section 17;
  - the earlier drafts' hashes, the tools' earlier versions' hashes, and the records' hashes;
  - which row names which output: two rows that swap their outputs and output hashes pass;
  - a table whose lines do not start with a pipe, such as one in a blockquote, and a row that does not;
  - a section cited in another form, such as a bare number outside section 17's "where" columns, and one cited
    just after a ".md" name, which it skips even if it means this study's;
  - whether a cited section is the right one;
  - question, rule, stage, refusal or cause numbers;
  - the Contents list against the headings, and duplicate headings;
  - its own printed counts, which it compares with nothing.
It checks its own hash, so it cannot vouch for itself. check_study_plants.py tests it.
It fails closed, naming what it read: a few forms read too much, such as "section 13, 2026-10-14", which it reads
as citing section 2026. The lead rewords them.

Usage: python -I check_study.py <path to QRO-0.md>
"""
import hashlib
import re
import sys
from pathlib import Path

if __name__ != "__main__":
    raise ImportError("a gate, not a module")
sys.stdout.reconfigure(errors="backslashreplace")                # a failure line must print, whatever it quotes

STUDY = Path(sys.argv[1])
QRO0 = STUDY.parent / "qro0"
text = STUDY.read_text(encoding="utf-8")
lines = text.splitlines()
failures = []
PIPE = re.compile(r"(?<!\\)\|")                                  # an unescaped pipe
NUM = r"\d+(?:\.\d+)?"


def flat(s):
    return re.sub(r"\s+", " ", s)


def section_span(number):
    """Top-level section `number`, from its heading to the next top-level heading, as (start, end) offsets."""
    m = re.search(rf"^## {number}\. .*?(?=^## \d+\. |\Z)", text, re.S | re.M)
    return (m.start(), m.end()) if m else (0, 0)


def section(number):
    start, end = section_span(number)
    return text[start:end]


def cells(row):
    """A row's cells, or None unless it starts and ends with an unescaped pipe."""
    parts = PIPE.split(row)
    if len(parts) < 3 or parts[0] != "" or parts[-1] != "":
        return None
    return parts[1:-1]


# 1. the draft numbers
m = re.search(r"\*\*Draft (\d+), \d{4}-\d{2}-\d{2}\.\*\*", text)
n = int(m.group(1)) if m else None
if n is None:
    failures.append("header: no 'Draft N, YYYY-MM-DD.' line")
else:
    head = flat(text[:text.index("## Contents")]) if "## Contents" in text else ""
    three = " ".join((head, flat(section(13)), flat(section(15))))
    for pattern, want, where, scope, every in (
            (r"\*\*Draft \d+\*\* answers", f"**Draft {n}** answers", "the header", head, True),
            (r"a re-check of draft \d+'s changes", f"a re-check of draft {n}'s changes", "the header", head, True),
            (r"Drafts 1 to \d+ went past verifiers, and draft \d+ goes next",
             f"Drafts 1 to {n - 1} went past verifiers, and draft {n} goes next", "section 13", flat(section(13)),
             True),
            (r"the re-checks of drafts 2 to \d+", f"the re-checks of drafts 2 to {n - 1}", "section 15",
             flat(section(15)), True),
            (r"what draft \d+ changed", f"what draft {n} changed", "section 17", flat(section(17)), False),
            (r"The instruments, in draft \d+", f"The instruments, in draft {n}", "section 17", flat(section(17)),
             False)):
        found = re.findall(pattern, scope)
        if want not in found:
            failures.append(f"{where}: no '{want}'")
        if every:                                            # a stale copy anywhere in the three places
            for stale in sorted(set(re.findall(pattern, three)) - {want}):
                failures.append(f"the header or section 13 or 15: a stale '{stale}'")

# 2. the tables
s17_start, s17_end = section_span(17)
s17_lines = (text[:s17_start].count("\n"), text[:s17_end].count("\n")) if s17_end else (0, 0)
tables = 0
where_cells = []                                             # (line number, cell) in section 17's "where" columns
i = 0
while i < len(lines):
    if not lines[i].strip().startswith("|"):
        i += 1
        continue
    j = i
    while j < len(lines) and lines[j].strip().startswith("|"):
        j += 1
    run = [lines[k].strip() for k in range(i, j)]
    if len(run) < 2 or not re.match(r"^\|\s*:?-{3,}", run[1]):
        for k in range(i, j):
            failures.append(f"line {k + 1}: a line starting with a pipe, in no table")
        i = j
        continue
    tables += 1
    rows = [cells(r) for r in run]
    for k, c in enumerate(rows):
        if c is None:
            failures.append(f"line {i + k + 1}: a table row that does not start and end with an unescaped pipe")
    if rows[0] is not None:
        for k, c in enumerate(rows[1:], start=1):
            if c is not None and len(c) != len(rows[0]):
                failures.append(f"line {i + k + 1}: a table row with {len(c)} cells, its header {len(rows[0])}")
    for c in rows[1] or []:
        if not re.fullmatch(r"\s*:?-{3,}:?\s*", c):
            failures.append(f"line {i + 2}: a delimiter cell '{c.strip()}', not three or more hyphens")
    if rows[0] is not None and s17_lines[0] <= i < s17_lines[1]:
        low = [h.strip().lower() for h in rows[0]]
        if "where" in low:
            w = low.index("where")
            where_cells += [(i + k + 1, c[w]) for k, c in enumerate(rows[2:], start=2) if c is not None and len(c) > w]
    i = j

# 3. the section references
headings = set()
for line in lines:
    h = re.match(rf"#{{2,3}} ({NUM})\.? ", line)
    if h:
        headings.add(h.group(1))
body = flat(text)
cited = set()
SEP = r"(?:,? and |,? or |, | to |/|-|–)"
for mm in re.finditer(rf"\b(?i:sections?) ({NUM}(?:{SEP}{NUM})*)", body):
    if re.search(r"\.md[,)]? ?$", body[max(0, mm.start() - 8):mm.start()]):
        continue                                             # another document's section
    for c in re.findall(NUM, mm.group(1)):
        cited.add(c)
        if c not in headings:
            failures.append(f"'{mm.group(0)}': section {c} is not a heading")
for line_no, cell in where_cells:
    for tok in re.split(r",\s*(?:and\s+)?|\s+and\s+", cell):
        if re.fullmatch(NUM, tok.strip()):
            cited.add(tok.strip())
            if tok.strip() not in headings:
                failures.append(f"line {line_no}: a \"where\" cell cites section {tok.strip()}, which is not a heading")

# 4. the instruments
s15 = section(15)
py_files = sorted(p.name for p in QRO0.iterdir() if p.is_file() and p.suffix == ".py")
row_lines = re.findall(r"^\| `[A-Za-z0-9_]+\.py` \|.*$", s15, re.M)
row_names = [re.match(r"^\| `([A-Za-z0-9_]+\.py)` \|", r).group(1) for r in row_lines]
for name in sorted({r for r in row_names if row_names.count(r) > 1}):
    failures.append(f"section 15: {name} has {row_names.count(name)} rows")
for name in sorted(set(py_files) - set(row_names)):
    failures.append(f"section 15: {name} is in {QRO0.name}/ but has no row")
for name in sorted(set(row_names) - set(py_files)):
    failures.append(f"section 15: a row names {name}, which is not in {QRO0.name}/")
outputs = set()
for line in row_lines:
    row = re.match(r"^\| `([A-Za-z0-9_]+\.py)` \| `([0-9a-f]{8})…`[^|]*\| ([^|]*) \| ([^|]*) \|$", line)
    if not row:
        failures.append(f"section 15: a row does not parse: {line[:60]}")
        continue
    name, prefix, output, out_hash = row.groups()
    path = QRO0 / name
    if path.is_file():
        got = hashlib.sha256(path.read_bytes()).hexdigest()[:8]
        if got != prefix:
            failures.append(f"section 15: {name} hashes {got}, the table says {prefix}")
    if ".out.txt" in output:
        out = re.fullmatch(r"`([A-Za-z0-9_]+\.out\.txt)`", output.strip())
        oh = re.fullmatch(r"`([0-9a-f]{8})…`", out_hash.strip())
        if not (out and oh):
            failures.append(f"section 15: {name}'s row names an output, but its output or hash cell does not parse")
            continue
        outputs.add(out.group(1))
        op = QRO0 / out.group(1)
        got = hashlib.sha256(op.read_bytes()).hexdigest()[:8] if op.is_file() else "missing"
        if got != oh.group(1):
            failures.append(f"section 15: {out.group(1)} hashes {got}, the table says {oh.group(1)}")
for entry in sorted(QRO0.iterdir()):
    if entry.is_dir():
        failures.append(f"{QRO0.name}/{entry.name}/: a directory")
    elif entry.suffix != ".py" and entry.name not in outputs:
        failures.append(f"{QRO0.name}/{entry.name}: a file no row names")

print(f"draft {n}: {tables} tables, {len(cited)} distinct sections cited, {len(row_names)} instrument rows "
      f"for {len(py_files)} instruments")
if failures:
    for f in failures:
        print(f"REFUSED: {f}")
    sys.exit(1)
print("ACCEPTED")
