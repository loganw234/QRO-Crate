"""P4's SHACL engine runner (P4's design, item 5). A script, never imported: the stage's tests run it as

    "$QRO_SHACL_PYTHON" -I tests/p4shacl/p4shacl_engine.py < request.json > response.json

with the interpreter of the virtual environment that holds pyshacl 0.40.1 and its seven pure-Python dependencies
(p4shacl_requirements.txt), outside the repository. It imports nothing of `qro` and nothing outside the standard
library and those wheels, so that what reads P4's shapes is the engine and not this repository.

  - Four calls are blocked in this process before pyshacl and rdflib are imported: the socket class's connect and
    connect_ex, and the module's create_connection and getaddrinfo, raise. The standard library's hashlib, json, socket and
    sys are imported first, for the guard and the request, and nothing else is; a test holds that order
    (tests/p4shacl/test_p4shacl_guard.py). The class itself stays a class, because
    replacing it with a function breaks ssl's import (MEASURED by the lead's smoke test, 2026-10-16). The tests
    hold the guard to a listening socket of their own: a connection that arrived would show. Other calls are open
    (gethostbyname, getfqdn, a UDP sendto: MEASURED on loopback by P4's verifier, round 1), and it found nothing in
    pyshacl or rdflib that uses them: the guard is these four calls, not "the network".
  - RO-Crate 1.3's context is never fetched. The request names the pinned copy and its SHA-256, and the runner
    refuses any other bytes; each crate's @context is rewritten, its URL replaced by that copy's definitions, before
    rdflib's JSON-LD parser reads it.
  - The request is JSON on stdin: {"context": {"path", "sha256"}, "base": IRI, "jobs": [...]}. Each job has an "id"
    and a "kind":
      "crate"    "metadata" (the crate's metadata as text), "shapes" (a list of file paths), optionally "inference"
                 (pyshacl's own: none, the default and the only one the shapes are for, rdfs, owlrl or both): the
                 crate's triples and the engine's report on them
      "graph"    "shapes" (Turtle text), "data" (N-Triples text), optionally "use_shapes" (shape IRIs): the report
      "meta"     "shapes" (a list of file paths, or Turtle text): the shapes against the SHACL-SHACL shapes
      "network"  "host", "port": whether a connection to them is refused in this process (a listener of the test's
                 sees no connection)
      "guard"    facts about the guard from inside: the socket class still a class, ssl still importing, and each of
                 the four calls the guard replaces raising the guard's own error
      "shapes"   "shapes" (file paths or text), "claims_predicate" (an IRI): the engine's reading of the shapes' names,
                 severities (a named shape's, and those of the property shapes it holds) and claims
  - The response is JSON on stdout, ASCII: {"engine": {...}, "results": [...]}, one result a job, in order. A job
    that fails answers {"id", "ok": false, "error"}, never an exception. A report is a list of {shape, severity,
    focus, component}, where `shape` is the named shape the result belongs to (a result of a property shape nested
    in a named shape is the named shape's), sorted, and `conforms` is the engine's own word.
"""
import hashlib
import json
import socket
import sys


def _blocked(*args, **kwargs):
    raise OSError("the network is blocked in this process")


socket.socket.connect = _blocked
socket.socket.connect_ex = _blocked
socket.create_connection = _blocked
socket.getaddrinfo = _blocked

import pyshacl  # noqa: E402
import rdflib  # noqa: E402
from rdflib.collection import Collection  # noqa: E402

SH = rdflib.Namespace("http://www.w3.org/ns/shacl#")
RDF = rdflib.RDF
CONTEXT_URL = "https://w3id.org/ro/crate/1.3/context"
_CACHE = {}


def local(term):
    return str(term).rsplit("#", 1)[-1] if term is not None else None


def term_json(t):
    if isinstance(t, rdflib.URIRef):
        return ["iri", str(t)]
    if isinstance(t, rdflib.BNode):
        return ["bnode", str(t)]
    return ["lit", str(t), str(t.datatype) if t.datatype is not None else "http://www.w3.org/2001/XMLSchema#string"]


def pinned_context(spec):
    if "context" not in _CACHE:
        data = open(spec["path"], "rb").read()
        if hashlib.sha256(data).hexdigest() != spec["sha256"]:
            raise ValueError("the context file is not the copy the request pins")
        _CACHE["context"] = json.loads(data)["@context"]
    return _CACHE["context"]


def shapes_graph(shapes, label=None):
    """A graph of shapes from file paths (a list) or from Turtle text (a string), parsed once per distinct input."""
    key = ("shapes", json.dumps(shapes, sort_keys=True))
    if key not in _CACHE:
        g = rdflib.Graph()
        if isinstance(shapes, list):
            for path in shapes:
                g.parse(path, format="turtle")
        else:
            g.parse(data=shapes, format="turtle")
        _CACHE[key] = g
    return _CACHE[key]


def parents(sg):
    """{nested shape: the shape that holds it}, through sh:property, sh:node, sh:not, sh:qualifiedValueShape and the
    lists of sh:or, sh:and and sh:xone."""
    out = {}
    for s, p, o in sg:
        if p in (SH.property, SH.node, SH["not"], SH.qualifiedValueShape):
            out.setdefault(o, s)
        elif p in (SH["or"], SH["and"], SH.xone):
            for item in Collection(sg, o):
                out.setdefault(item, s)
    return out


def named(shape, up):
    seen = set()
    while isinstance(shape, rdflib.BNode) and shape in up and shape not in seen:
        seen.add(shape)
        shape = up[shape]
    return str(shape) if isinstance(shape, rdflib.URIRef) else None


INFERENCE = ("none", "rdfs", "owlrl", "both")


def report(sg, dg, use_shapes=None, inference="none"):
    """pyshacl's report on `dg` against `sg`. `inference` is pyshacl's own argument: the shapes are for none, its default, and a
    job names another only to hold what the others do to them (limit 2)."""
    if inference not in INFERENCE:
        raise ValueError(f"inference is one of {', '.join(INFERENCE)}")
    conforms, rg, _ = pyshacl.validate(dg, shacl_graph=sg, inference=inference, advanced=False, allow_warnings=True,
                                       allow_infos=True, use_shapes=use_shapes)
    if not isinstance(rg, rdflib.Graph):
        raise ValueError(f"the engine failed: {rg}")
    up = parents(sg)
    results = []
    for r in rg.subjects(RDF.type, SH.ValidationResult):
        focus = rg.value(r, SH.focusNode)
        results.append({"shape": named(rg.value(r, SH.sourceShape), up), "severity": local(rg.value(r, SH.resultSeverity)),
                        "focus": "_:blank" if isinstance(focus, rdflib.BNode) else str(focus),
                        "component": local(rg.value(r, SH.sourceConstraintComponent))})
    results.sort(key=lambda d: (str(d["shape"]), d["severity"], d["focus"], str(d["component"])))
    return {"conforms": bool(conforms), "results": results}


def crate_job(job, request):
    md = json.loads(job["metadata"])
    ctx = md["@context"]
    if not isinstance(ctx, list) or ctx[0] != CONTEXT_URL:
        raise ValueError("the crate's @context does not begin with RO-Crate 1.3's")
    md["@context"] = [pinned_context(request["context"])] + ctx[1:]
    dg = rdflib.Graph()
    dg.parse(data=json.dumps(md), format="json-ld", publicID=request["base"])
    triples = sorted([term_json(s), str(p), term_json(o)] for s, p, o in dg)
    out = report(shapes_graph(job["shapes"]), dg, inference=job.get("inference", "none"))
    out["triples"] = triples
    return out


def graph_job(job, request):
    dg = rdflib.Graph()
    dg.parse(data=job["data"], format="nt")
    use = [rdflib.URIRef(u) for u in job["use_shapes"]] if job.get("use_shapes") else None
    return report(shapes_graph(job["shapes"]), dg, use)


def meta_job(job, request):
    """The shapes graph against the SHACL-SHACL shapes that ship with pyshacl, as pyshacl's own meta_shacl does it
    (with rdfs inference, which those shapes rely on): is what the writer wrote SHACL?"""
    from pyshacl.entrypoints import meta_validate
    conforms, _, text = meta_validate(shapes_graph(job["shapes"]), inference="rdfs")
    return {"conforms": bool(conforms), "text": text[:2000]}


def network_job(job, request):
    try:
        socket.create_connection((job["host"], job["port"]), timeout=2)
    except OSError as x:
        return {"blocked": str(x) == "the network is blocked in this process", "error": str(x)}
    return {"blocked": False, "error": ""}


def guard_job(job, request):
    """Facts about the guard, from inside the process it guards: the socket class is still a class, ssl still imports
    (it subclasses it), and each of the four calls the guard replaces raises the guard's own error."""
    import ssl
    calls = {"connect": lambda s: s.connect(("127.0.0.1", 9)), "connect_ex": lambda s: s.connect_ex(("127.0.0.1", 9)),
             "create_connection": lambda s: socket.create_connection(("127.0.0.1", 9)),
             "getaddrinfo": lambda s: socket.getaddrinfo("example.invalid", 80)}
    blocked = {}
    for name, call in calls.items():
        with socket.socket() as s:
            try:
                call(s)
                blocked[name] = False
            except OSError as x:
                blocked[name] = str(x) == "the network is blocked in this process"
    own = {"connect": socket.socket.connect, "connect_ex": socket.socket.connect_ex,
           "create_connection": socket.create_connection, "getaddrinfo": socket.getaddrinfo}
    return {"socket_is_a_class": isinstance(socket.socket, type), "ssl_imports": bool(ssl.OPENSSL_VERSION),
            "blocked": blocked, "replaced": {name: fn is _blocked for name, fn in own.items()}}


def shapes_job(job, request):
    """The engine's reading of the shapes' severities: each named shape's, and those of the property shapes it holds."""
    sg = shapes_graph(job["shapes"])
    claims = rdflib.URIRef(job["claims_predicate"])
    out = {}
    for kind in (SH.NodeShape, SH.PropertyShape):
        for s in sg.subjects(RDF.type, kind):
            if isinstance(s, rdflib.URIRef):
                out[str(s)] = {"severity": local(sg.value(s, SH.severity)),
                               "properties": sorted(str(local(sg.value(p, SH.severity)))
                                                    for p in sg.objects(s, SH.property)),
                               "claims": sorted(str(c) for c in sg.objects(s, claims))}
    return {"shapes": out, "triples": len(sg)}


KINDS = {"crate": crate_job, "graph": graph_job, "meta": meta_job, "network": network_job, "guard": guard_job,
         "shapes": shapes_job}


def main():
    request = json.loads(sys.stdin.read())
    out = {"engine": {"pyshacl": pyshacl.__version__, "rdflib": rdflib.__version__}, "results": []}
    for job in request["jobs"]:
        try:
            got = KINDS[job["kind"]](job, request)
            out["results"].append(dict(got, id=job["id"], ok=True))
        except Exception as x:
            out["results"].append({"id": job.get("id"), "ok": False, "error": f"{type(x).__name__}: {x}"[:1500]})
    sys.stdout.write(json.dumps(out, ensure_ascii=True, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
