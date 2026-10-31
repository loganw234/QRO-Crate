"""The runner's guard blocks the four calls it names (P4's design, item 5): connect, connect_ex, create_connection and
getaddrinfo, installed before pyshacl and rdflib are imported (the standard library's hashlib, json, socket and sys come first),
and held here to a listening socket of the test's own. Other calls are open, and P4's verifier found nothing the engine runs
that uses them (docs/P4.md). A quiet listener proves nothing unless the same listener hears a connection that is let through, so
the control comes first: the same connection from an interpreter with no guard arrives.

Two things the first verifier's guard tests did not hold, which P4's second verifier found by taking them away (a note of its
report, round 2): `-I` in `run_engine`, which a module on the path the environment names would otherwise replace pyshacl by, and
the guard's place before the engine's imports, held as the order of the runner's statements."""
import ast
import socket
import subprocess

import pytest
from p4shacl_helpers import RUNNER, engine_python, run_engine


@pytest.fixture
def listener():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    s.listen(5)
    s.settimeout(1.5)
    yield s
    s.close()


def connects(listener):
    """Whether a connection arrived at the listener while this ran."""
    try:
        conn, _ = listener.accept()
    except socket.timeout:
        return False
    conn.close()
    return True


def test_the_control_a_connection_that_is_let_through_arrives_at_the_listener(listener):
    port = listener.getsockname()[1]
    code = f"import socket; socket.create_connection(('127.0.0.1', {port}), timeout=5).close()"
    done = subprocess.run([engine_python(), "-I", "-c", code], capture_output=True, text=True, timeout=60)
    assert done.returncode == 0, done.stderr[-300:]
    assert connects(listener)


def test_the_runner_is_refused_a_connection_to_the_listener_and_none_arrives(listener):
    port = listener.getsockname()[1]
    answers, _ = run_engine([{"id": "n", "kind": "network", "host": "127.0.0.1", "port": port}])
    assert answers["n"]["ok"] and answers["n"]["blocked"] is True, answers["n"]
    assert answers["n"]["error"] == "the network is blocked in this process"
    assert not connects(listener)


def test_a_name_is_never_looked_up_either():
    answers, _ = run_engine([{"id": "n", "kind": "network", "host": "example.invalid", "port": 80}])
    assert answers["n"]["blocked"] is True and answers["n"]["error"] == "the network is blocked in this process"


def test_the_guard_replaces_the_four_calls_and_leaves_the_socket_a_class_so_that_ssl_still_imports():
    answers, _ = run_engine([{"id": "g", "kind": "guard"}])
    g = answers["g"]
    assert g["ok"] and g["socket_is_a_class"] is True and g["ssl_imports"] is True
    assert g["blocked"] == {"connect": True, "connect_ex": True, "create_connection": True, "getaddrinfo": True}
    assert g["replaced"] == {"connect": True, "connect_ex": True, "create_connection": True, "getaddrinfo": True}   # each is the guard's


POISON = "raise RuntimeError('the environment names a path, and the interpreter read it')\n"


def poisoned(tmp_path, monkeypatch):
    """A directory with a pyshacl.py and an rdflib.py that fail on import, named by PYTHONPATH."""
    for name in ("pyshacl", "rdflib"):
        (tmp_path / f"{name}.py").write_text(POISON, encoding="ascii")
    monkeypatch.setenv("PYTHONPATH", str(tmp_path))


def test_the_control_without_isolation_the_interpreter_reads_the_path_the_environment_names(tmp_path, monkeypatch):
    poisoned(tmp_path, monkeypatch)
    done = subprocess.run([engine_python(), "-c", "import rdflib"], capture_output=True, text=True, timeout=60)
    assert done.returncode != 0 and "the environment names a path" in done.stderr, done.stderr[-300:]


def test_the_runner_is_run_isolated_so_that_a_path_in_the_environment_is_never_read(tmp_path, monkeypatch):
    """`run_engine` passes -I: the engine is the wheels' and not what PYTHONPATH, the user site or the working directory name."""
    poisoned(tmp_path, monkeypatch)
    answers, versions = run_engine([{"id": "g", "kind": "guard"}])
    assert answers["g"]["ok"] is True and versions == {"pyshacl": "0.40.1", "rdflib": "7.6.0"}


GUARDED = {"socket.socket.connect", "socket.socket.connect_ex", "socket.create_connection", "socket.getaddrinfo"}


def test_the_four_calls_are_blocked_before_pyshacl_and_rdflib_are_imported_and_only_four_modules_come_first():
    """The runner is a script, so the order of its statements is the order it runs in: the four assignments of the guard
    come before the first import of the engine, and the imports before them are hashlib, json, socket and sys."""
    guard, before, engine = [], [], []
    for i, node in enumerate(ast.parse(RUNNER.read_text(encoding="utf-8")).body):
        if isinstance(node, ast.Assign) and ast.unparse(node.targets[0]) in GUARDED:
            guard.append((i, ast.unparse(node.targets[0])))
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            top = {n.split(".")[0] for n in ([a.name for a in node.names] if isinstance(node, ast.Import) else [node.module])}
            (engine if top & {"pyshacl", "rdflib"} else before).append((i, top))
    assert {name for _, name in guard} == GUARDED and len(guard) == 4 and len(engine) == 3        # pyshacl, rdflib, rdflib.collection
    assert max(i for i, _ in guard) < min(i for i, _ in engine)
    assert {m for i, top in before if i < min(i for i, _ in engine) for m in top} == {"hashlib", "json", "socket", "sys"}


def test_a_crate_whose_context_is_not_rocrates_is_refused_by_the_runner_not_fetched():
    md = '{"@context": ["https://example.org/elsewhere", {}], "@graph": []}'
    answers, _ = run_engine([{"id": "c", "kind": "crate", "metadata": md, "shapes": []}])
    assert answers["c"]["ok"] is False and "does not begin with RO-Crate 1.3's" in answers["c"]["error"]


def test_a_context_that_is_not_the_pinned_copy_is_refused(tmp_path):
    import json
    from p4shacl_helpers import ROOT, engine_python as py
    from qro import vocabulary as V
    fake = tmp_path / "context.jsonld"
    fake.write_bytes(b'{"@context": {}}')
    request = {"context": {"path": str(fake), "sha256": V.ROCRATE_CONTEXT_SHA256}, "base": "file:///crate/",
               "jobs": [{"id": "c", "kind": "crate", "metadata": json.dumps({"@context": [
                   "https://w3id.org/ro/crate/1.3/context"], "@graph": []}), "shapes": []}]}
    done = subprocess.run([py(), "-I", str(ROOT / "tests" / "p4shacl" / "p4shacl_engine.py")], input=json.dumps(request),
                          capture_output=True, text=True, timeout=120)
    answer = json.loads(done.stdout)["results"][0]
    assert answer["ok"] is False and "not the copy the request pins" in answer["error"]
