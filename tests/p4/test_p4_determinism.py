"""Generation is deterministic (P4's design, item 8): two renders, from two working directories and two hash seeds, are the same
bytes; and nothing in them is read from a clock, a path, a user or a host. A set iterated into output would show under a
second hash seed; a path or a time written into a file would show as the host's own."""
import hashlib
import json
import os
import socket
import subprocess
import sys
import tempfile
from pathlib import Path

from p4_helpers import ROOT
from qro import p4_profile as P

DRIVER = """import hashlib, json, sys
sys.dont_write_bytecode = True
sys.path.insert(0, sys.argv[1])
from qro import p4_profile
files = p4_profile.render(sys.argv[1])
print(json.dumps({k: hashlib.sha256(v).hexdigest() for k, v in sorted(files.items())}))
"""


def digests(files):
    return {k: hashlib.sha256(v).hexdigest() for k, v in sorted(files.items())}


def test_two_renders_in_one_process_are_the_same_bytes():
    assert P.render() == P.render()


def test_two_renders_from_two_working_directories_are_the_same_bytes(tmp_path, monkeypatch):
    first = P.render()
    for name in ("one", "two"):
        (tmp_path / name).mkdir()
        monkeypatch.chdir(tmp_path / name)
        assert P.render() == first


def test_two_renders_under_three_hash_seeds_and_three_working_directories_are_the_same_bytes(tmp_path):
    driver = tmp_path / "driver.py"
    driver.write_text(DRIVER, encoding="ascii")
    want = digests(P.render())
    for seed, name in (("0", "a"), ("1", "b"), ("2718281828", "c")):
        (tmp_path / name).mkdir()
        done = subprocess.run([sys.executable, str(driver), str(ROOT)], cwd=tmp_path / name, capture_output=True, text=True,
                              env=dict(os.environ, PYTHONHASHSEED=seed, PYTHONDONTWRITEBYTECODE="1", LC_ALL="C",
                                       PYTHONIOENCODING="cp1252"))
        assert done.returncode == 0, done.stderr[-500:]
        assert json.loads(done.stdout) == want, seed


def forms(path):
    """A path as it may be written: native, with slashes, with doubled backslashes, and as git bash has it."""
    p = str(path)
    out = {p, p.replace("\\", "/"), p.replace("\\", "\\\\")}
    if len(p) > 2 and p[1] == ":":
        out.add("/" + p[0].lower() + p[2:].replace("\\", "/"))
    return {x for x in out if len(x) > 4}


def test_no_path_of_this_host_and_no_host_name_is_in_any_file():
    files = {**P.render(), P.CONTEXT: P.read_context()}
    leaks = forms(ROOT) | forms(Path(tempfile.gettempdir())) | forms(Path.home()) | forms(Path.cwd())
    name = socket.gethostname()
    for path, data in files.items():
        text = data.decode("ascii")
        for leak in leaks:
            assert leak not in text, (path, leak)
        if len(name) >= 5:
            assert name.lower() not in text.lower(), (path, "the host's name")


def test_no_time_of_the_clock_is_in_any_file_the_dates_are_the_constants():
    import re
    files = P.render()
    stamps = set()
    for path, data in files.items():
        stamps |= set(re.findall(r"\b20[0-9]{2}-[01][0-9]-[0-3][0-9]T[0-2][0-9]:[0-5][0-9]:[0-5][0-9]", data.decode("ascii")))
    assert stamps <= {"2026-10-14T00:00:00"}                          # the fixture's constant writtenAt, and nothing else
    assert P.DATE_PUBLISHED in files[P.DESCRIPTION].decode() and "datePublished" in files["ro-crate-metadata.json"].decode()


P4_FILES = sorted((ROOT / "qro").glob("p4_*.py")) + [ROOT / "tools" / "gen_profile.py"]
CLOCK_MODULES = {"time", "datetime"}
CLOCK_CALLS = {"today", "now", "utcnow", "time_ns", "localtime", "gmtime", "strftime", "monotonic", "perf_counter", "fromtimestamp"}


def test_no_file_of_p4_reads_a_clock():
    """P4's verifier, round 1, defect 6: DATE_PUBLISHED taken from the clock passed the old test on the day it was run."""
    import ast
    assert len(P4_FILES) == 8
    for path in P4_FILES:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        imported = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported |= {a.name.split(".")[0] for a in node.names}
            elif isinstance(node, ast.ImportFrom):
                imported.add((node.module or "").split(".")[0])
        called = {n.attr for n in ast.walk(tree) if isinstance(n, ast.Attribute)}
        assert not imported & CLOCK_MODULES and not called & CLOCK_CALLS, (path.name, imported & CLOCK_MODULES, called & CLOCK_CALLS)


def test_the_published_date_is_a_literal_of_the_source_and_the_clock_changes_nothing(monkeypatch):
    """The constant is a string literal in the source; and the module, run again under each of two clocks (the 3rd of
    February 2001, the 31st of December 2099), has the same constant."""
    import ast
    import datetime
    import importlib.util
    import time
    from qro import spelling as S
    source = Path(P.__file__).read_text(encoding="utf-8")
    literals = [n.value.value for n in ast.parse(source).body if isinstance(n, ast.Assign) and isinstance(n.value, ast.Constant)
                and any(isinstance(t, ast.Name) and t.id == "DATE_PUBLISHED" for t in n.targets)]
    assert len(literals) == 1 and isinstance(literals[0], str) and S.problem("date", literals[0]) is None, literals
    assert P.DATE_PUBLISHED == literals[0]
    real_strftime = time.strftime
    for day in (datetime.date(2001, 2, 3), datetime.date(2099, 12, 31)):
        stamp = datetime.datetime(day.year, day.month, day.day, 4, 5, 6)

        class FakeDate(datetime.date):
            @classmethod
            def today(cls, day=day):
                return cls(day.year, day.month, day.day)

        class FakeDateTime(datetime.datetime):
            @classmethod
            def now(cls, tz=None, stamp=stamp):
                return cls(stamp.year, stamp.month, stamp.day, 4, 5, 6)
            utcnow = today = now

        with monkeypatch.context() as mp:
            mp.setattr(datetime, "date", FakeDate)
            mp.setattr(datetime, "datetime", FakeDateTime)
            mp.setattr(time, "time", lambda stamp=stamp: stamp.timestamp())
            mp.setattr(time, "strftime", lambda fmt, t=None, stamp=stamp: real_strftime(fmt, t or stamp.timetuple()))
            spec = importlib.util.spec_from_file_location("p4_profile_under_a_clock", P.__file__)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
        assert module.DATE_PUBLISHED == literals[0], day
