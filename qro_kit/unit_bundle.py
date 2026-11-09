"""The unit's bundle: Quantum-Film's hardware bundle for the unit's plan, written and held (P5's design, items 1 and 2; P5.1).

Adapted from moth-quantum's tools/hw_bundle.py (main) and quantum_film/ibm/bundle.py (`check`, `_top_problems`,
`_jobs_problems`) at 3a73823, which are held to v0's plan (bundle.py:383-385 names v0's jobs, :407-408 takes its shots) and so
cannot hold the unit's. What changed, and only that: the plan is the unit's (qro.p5_unit.jobs_of_device: six jobs, a control
job and a film job in each of three passes), the circuits are five (the known answer's complement is the fifth), a circuit's
files are shared by every job that runs it while each job's entry has a salt and a commitment of its own, the options are the
recipe's (the device's rep_delay beside them), and the manifest carries a `unit` block. Everything else is the vendored code's:
the logical circuits' text, the gate lists, the ISA check, the commitment, the manifest's canonical text.

`write` freezes one device's bundle against a backend; `check` holds a bundle directory to its manifest, file by file, the
logical circuits to the source, the unit's plan, the chain, the SWAP-free checks, the ISA check and the commitments.
Third-party imports are inside functions, after `_qf.load()`.
"""
import importlib.metadata
import io
import os
import platform
from pathlib import Path

from qro import p5_unit as U
from qro_kit import _qf

QISKIT, RUNTIME = "2.5.2", "0.50.0"
CZ = {"known-answer": 0, "known-complement": 0, "law": 102, "coherence-xx": 102, "coherence-yy": 102}
ROTATION_GATES = {"law": (), "coherence-xx": (("h", 0), ("h", 1)), "coherence-yy": (("sdg", 0), ("h", 0), ("sdg", 1), ("h", 1))}
EXTENSIONS = {"qasm": "circuit", "qpy": "isa", "gates.json": "gates", "isa.qasm3": "qasm3"}
FIELDS = ("format", "stock", "kind", "route", "backend", "program", "decode", "options", "options_sha256", "known_answer",
          "pair", "source", "target", "compile", "versions", "frozen_at", "readme_sha256", "jobs", "unit")


class BundleError(ValueError):
    """The bundle cannot be written or does not hold."""


def circuit_order():
    """The five circuits of a bundle, in the order their files are written: (name, role, basis)."""
    seen = {}
    for kind in U.KINDS_OF_JOB:
        for name, role, basis in U.CIRCUITS[kind]:
            seen.setdefault(name, (role, basis))
    return [(n, r, b) for n, (r, b) in seen.items()]


def calibration_of(backend):
    """The backend's calibration stamp as a UTC time, or the words it states none in."""
    import datetime
    try:
        when = getattr(backend.properties(), "last_update_date", None)
    except Exception:
        when = None
    if when is None:
        return "not stated by the backend"
    if when.tzinfo is None:
        when = when.replace(tzinfo=datetime.timezone.utc)
    return when.astimezone(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def errors_of(target, doc):
    out = {}
    for name, qs, _c, _p in doc["gates"]:
        if name == "barrier":
            continue
        try:
            props = target[name][tuple(qs)]
        except KeyError:
            continue
        if props is not None and props.error is not None:
            out[f"{name}:{','.join(map(str, qs))}"] = float(props.error)
    return out


def defaulted_options(sent):
    """The fields of SamplerOptions the client leaves to the server: every leaf of its defaults the options as sent do not
    state (max_execution_time is a runtime option, stated beside them in each job's entry)."""
    from dataclasses import asdict

    from qiskit_ibm_runtime.options import SamplerOptions

    def leaves(d, prefix=""):
        for k, v in d.items():
            if k.startswith("_"):
                continue
            if isinstance(v, dict):
                yield from leaves(v, f"{prefix}{k}.")
            else:
                yield f"{prefix}{k}"
    sent_keys = set(leaves(sent))
    return sorted(k for k in leaves(asdict(SamplerOptions())) if k not in sent_keys and k != "max_execution_time")


def readme(m):
    jobs = "\n".join(f"- `{j['job']}`: " + ", ".join(f"{e['name']} ({e['shots']:,} shots)" for e in j["circuits"])
                     + f"; at most {j['max_execution_time']} s of QPU time." for j in m["jobs"])
    return "\n".join([
        f"# QRO-Crate unit bundle: {m['stock']} on {m['backend']}", "",
        "This directory is a frozen bundle of the free-tier unit's recipe " + f"{m['unit']['recipe']}. It fixes completely "
        "what will run on this device: change nothing in it. Its identity is the SHA-256 of `manifest.json`, which every job "
        "line names; the unit's is the SHA-256 of `../../UNIT.json`'s bytes.", "",
        f"- Backend `{m['backend']}` (kind `{m['kind']}`), route `{m['route']}`, program `{m['program']}`.",
        f"- Compiled at optimization level {m['compile']['optimization_level']} with seed {m['compile']['seed_transpiler']}, "
        f"against the target's calibration of {m['target']['calibration']}.",
        f"- The chain, the physical qubits of logical qubits 0 to {U.M - 1}: {m['jobs'][0]['circuits'][0]['chain']}.",
        "- Options, stated: dynamical decoupling off, gate twirling off, measurement twirling off, qubits initialised each shot.",
        "", "## The jobs, in order", "", jobs, "",
        f"The known answer puts X on {m['known_answer']}, its complement on the other qubits: the control job checks the "
        "order in which the device's bitstrings are read. A film job is submitted only after its pass's control job holds on "
        "both of its PUBs. A job is submitted once.", ""])


def write(out_dir, backend, kind, divisor, seed, source_text):
    """Freeze one device's bundle into `out_dir` (made if absent, empty): the manifest as a dict and its SHA-256."""
    q = _qf.load("fixer", "bundle", "decode", "isa", "runner")
    import qiskit
    import qiskit_ibm_runtime
    from qiskit import QuantumCircuit, qasm2, qasm3, qpy
    from qiskit.transpiler import generate_preset_pass_manager

    from qro_kit import submit
    out = Path(out_dir)
    if out.exists() and any(out.iterdir()):
        raise BundleError(f"{out} is not empty: a bundle is written once, into a new directory")
    if (qiskit.__version__, qiskit_ibm_runtime.__version__) != (QISKIT, RUNTIME):
        raise BundleError(f"qiskit {qiskit.__version__} and qiskit-ibm-runtime {qiskit_ibm_runtime.__version__}: the kit is "
                         f"pinned to {QISKIT} and {RUNTIME}")
    if q.runner.kind_from(False, False, True) != kind:
        raise BundleError("the local route freezes kind simulator only (a fake backend is never a qpu)")
    target = backend.target
    edges = sorted({tuple(sorted(e)) for e in backend.coupling_map.get_edges()})
    logical = {}
    for name, _role, _basis in circuit_order():
        text = U.logical_qasm(name, source_text)
        c = qasm2.loads(text)
        if name in ("known-answer", "known-complement"):
            built = QuantumCircuit(U.M)
            for qubit in (U.KNOWN_ANSWER if name == "known-answer" else U.KNOWN_COMPLEMENT):
                built.x(qubit)
        else:
            built = qasm2.loads(source_text)
            for gate, qubit in ROTATION_GATES[name]:
                getattr(built, gate)(qubit)
        built.measure_all()
        if c != built:
            raise BundleError(f"{name}: qiskit does not read the derived text as the circuit measure_all builds")
        c.name = name
        logical[name] = (text, c)

    def compile_(c, chain=None):
        return generate_preset_pass_manager(optimization_level=q.bundle.OPTIMIZATION_LEVEL, backend=backend,
                                            seed_transpiler=seed, initial_layout=chain).run(c)
    transpiled = {"law": compile_(logical["law"][1])}
    chain = transpiled["law"].layout.initial_index_layout(filter_ancillas=True)
    for name, _r, _b in circuit_order():
        if name != "law":
            transpiled[name] = compile_(logical[name][1], chain)

    config = backend.configuration()
    rep_delay = getattr(config, "default_rep_delay", None) if getattr(config, "dynamic_reprate_enabled", False) else None
    sampler, sent = submit.sampler_for(backend, 1, rep_delay)
    want_options = dict(U.OPTIONS)
    if rep_delay is not None:
        want_options = {**U.OPTIONS, "execution": {**U.OPTIONS["execution"], "rep_delay": rep_delay}}
    if not q.bundle.same_json(sent, want_options):
        raise BundleError(f"SamplerV2 would send the options {sent}, not the recipe's {want_options}")
    del sampler

    files, values, docs = {}, {}, {}
    for name, role, basis in circuit_order():
        t = transpiled[name]
        doc = q.isa.gate_list(t)
        bad = q.isa.read(doc) or q.isa.swap_free(doc, edges, CZ[name])
        if bad:
            raise BundleError(f"{name}: " + "; ".join(bad))
        answer = U.KNOWN_COMPLEMENT if name == "known-complement" else U.KNOWN_ANSWER
        held, values[name] = q.bundle.hold_isa(doc, "known-answer" if role == "known-answer" else name, role, basis,
                                                source_text, answer)
        if held:
            raise BundleError(f"{name}: " + "; ".join(held))
        parts = {"circuit": logical[name][0].encode("ascii"), "gates": q.bundle.text(doc).encode("ascii"),
                 "qasm3": qasm3.dumps(t).encode("ascii")}
        buf = io.BytesIO()
        qpy.dump(t, buf)
        parts["isa"] = buf.getvalue()
        again = qpy.load(io.BytesIO(parts["isa"]))[0]
        if not q.bundle.same_json(q.isa.gate_list(again), doc):
            raise BundleError(f"{name}: the QPY file does not read back as the gate list")
        files[name], docs[name] = parts, doc
    out.mkdir(parents=True, exist_ok=True)
    for name, parts in files.items():
        for part, suffix in q.bundle.SUFFIX.items():
            (out / (name + suffix)).write_bytes(parts[part])
    manifest = {
        "format": q.bundle.FORMAT, "stock": U.STOCK, "kind": kind, "route": U.ROUTE, "backend": backend.name,
        "program": U.PROGRAM, "decode": q.decode.DECODE, "options": sent, "options_sha256": q.fixer.options_digest(sent),
        "known_answer": list(U.KNOWN_ANSWER), "pair": list(U.PAIR),
        "source": {"path": U.SOURCE_PATH, "sha256": U.SOURCE_SHA256},
        "target": {"name": backend.name, "num_qubits": int(target.num_qubits), "calibration": calibration_of(backend),
                   "coupling": [list(e) for e in edges]},
        "compile": {"optimization_level": q.bundle.OPTIMIZATION_LEVEL, "seed_transpiler": seed,
                    "layout": "the law's, chosen at level 2 against this target's calibration; the other circuits pinned to it"},
        "versions": {"python": platform.python_version(), "qiskit": qiskit.__version__,
                     "qiskit_ibm_runtime": qiskit_ibm_runtime.__version__,
                     "qiskit_aer": importlib.metadata.version("qiskit-aer"),
                     "numpy": importlib.metadata.version("numpy"), "qpy": str(qpy.QPY_VERSION),
                     "quantum_film": __import__("quantum_film").__version__},
        "frozen_at": q.bundle.utc_now(), "readme_sha256": None, "jobs": [],
        "unit": {"recipe": U.RECIPE_NAME, "recipe_sha256": U.recipe_sha256(divisor), "shots_divisor": divisor,
                 "device_order": list(U.DEVICE_SETS[kind]), "options_defaulted": defaulted_options(sent)}}
    for jname, k, _p, pubs in U.jobs_of_device(divisor):
        entries = []
        for pub, cname, role, basis, shots in pubs:
            parts, doc = files[cname], docs[cname]
            e = {"pub": pub, "name": cname, "role": role, "basis": basis, "shots": shots,
                 "source_sha256": None if role == "known-answer" else U.SOURCE_SHA256,
                 "circuit_sha256": q.bundle.sha256(parts["circuit"]), "isa_sha256": q.bundle.sha256(parts["isa"]),
                 "gates_sha256": q.bundle.sha256(parts["gates"]), "qasm3_sha256": q.bundle.sha256(parts["qasm3"]),
                 "chain": doc["layout"]["initial"], "esp": q.isa.esp(doc, errors_of(target, doc)),
                 "isa": values[cname], "salt": os.urandom(32).hex(), "commitment": None}
            entries.append(e)
        manifest["jobs"].append({"job": jname, "max_execution_time": U.CAPS[k], "circuits": entries})
    for j in manifest["jobs"]:
        for e in j["circuits"]:
            e["commitment"] = q.bundle.commitment(manifest, e)
    text = readme(manifest).encode("ascii")
    (out / q.bundle.README).write_bytes(text)
    manifest["readme_sha256"] = q.bundle.sha256(text)
    data = q.bundle.text(manifest).encode("ascii")
    (out / q.bundle.MANIFEST).write_bytes(data)
    m, digest, problems = check(out, source_text, divisor, kind)
    if problems:
        raise BundleError("the bundle written does not hold:\n  " + "\n  ".join(problems))
    return manifest, digest


def check(bundle_dir, source_text, divisor, kind):
    """(manifest, its SHA-256, the named reasons the bundle is refused); [] means every file is the manifest's, every logical
    circuit is derived from the source, the manifest is the unit's plan, every PUB has a salt and a commitment of its own,
    and every transpiled circuit passes the SWAP-free and ISA checks."""
    q = _qf.load("fixer", "bundle", "decode", "isa")
    bundle_dir = Path(bundle_dir)
    try:
        m, digest = q.bundle.load(bundle_dir)
    except (OSError, UnicodeDecodeError, ValueError, RecursionError) as e:
        return None, None, [f"manifest.json: unreadable ({type(e).__name__}: {e})"[:300]]
    if not isinstance(m, dict) or sorted(m) != sorted(FIELDS):
        return m, digest, [f"manifest.json: fields {sorted(m) if isinstance(m, dict) else type(m).__name__}; a unit "
                           f"bundle's manifest carries exactly {sorted(FIELDS)}"]
    out = _top_problems(q, m, divisor, kind)
    out += _jobs_problems(q, m, divisor)
    if out:
        return m, digest, out
    named = q.bundle.files(m)
    extra = sorted(set(p.name for p in bundle_dir.iterdir()) - set(named) - {q.bundle.MANIFEST})
    if extra:
        out.append(f"files: {extra} are in the bundle and not in its manifest")
    for name, want in sorted(named.items()):
        try:
            got = q.bundle.sha256((bundle_dir / name).read_bytes())
        except OSError:
            out.append(f"{name}: missing")
            continue
        if got != want:
            out.append(f"{name}: its SHA-256 is not the manifest's")
    if out:
        return m, digest, out
    edges = [tuple(e) for e in m["target"]["coupling"]]
    chains, salts, commitments, held = set(), [], [], {}
    for j in m["jobs"]:
        for e in j["circuits"]:
            where = f"{j['job']}[{e['pub']}] {e['name']}"
            if (bundle_dir / (e["name"] + ".qasm")).read_bytes() != U.logical_qasm(e["name"], source_text).encode("ascii"):
                out.append(f"{where}: the logical circuit is not the one derived from the source")
            raw = (bundle_dir / (e["name"] + ".gates.json")).read_bytes()
            try:
                doc = q.bundle.load_json(raw)
            except (UnicodeDecodeError, ValueError, RecursionError) as ex:
                out.append(f"{where}: the gate list is unreadable ({type(ex).__name__})")
                continue
            if raw != q.bundle.text(doc).encode("ascii"):
                out.append(f"{where}: the gate list's bytes are not its canonical text")
            problems = q.isa.read(doc)
            if problems:
                out += [f"{where}: {p}" for p in problems[:5]]
                continue
            if doc["layout"]["initial"] != e["chain"] or doc["num_clbits"] != U.M:
                out.append(f"{where}: the gate list's chain is not the manifest's, or it measures other than {U.M} bits")
            chains.add(tuple(e["chain"]))
            out += [f"{where}: {p}" for p in q.isa.swap_free(doc, edges, CZ[e["name"]])]
            key = (e["name"], q.bundle.sha256(raw))
            if key not in held:
                answer = U.KNOWN_COMPLEMENT if e["name"] == "known-complement" else U.KNOWN_ANSWER
                try:
                    held[key] = q.bundle.hold_isa(doc, "known-answer" if e["role"] == "known-answer" else e["name"],
                                                  e["role"], e["basis"], source_text, answer)[0]
                except (q.isa.IsaRefusal, ValueError) as ex:
                    held[key] = [f"isa: {ex}"]
            out += [f"{where}: {p}" for p in held[key]]
            if e["commitment"] != q.bundle.commitment(m, e):
                out.append(f"{where}: the commitment does not recompute from the manifest's fields")
            salts.append(e["salt"])
            commitments.append(e["commitment"])
    if len(chains) > 1:
        out.append(f"chain: the circuits are on {len(chains)} different chains; a bundle runs every circuit on the law's")
    if len(set(salts)) != len(salts) or len(set(commitments)) != len(commitments):
        out.append("salt: every PUB of every job has its own salt and commitment")
    return m, digest, out


def _top_problems(q, m, divisor, kind):
    out = []
    if m["format"] != q.bundle.FORMAT:
        out.append(f"format: {m['format']!r} is not {q.bundle.FORMAT!r}")
    for field, want in (("stock", U.STOCK), ("program", U.PROGRAM), ("decode", U.DECODE), ("route", U.ROUTE), ("kind", kind)):
        if m[field] != want:
            out.append(f"{field}: {m[field]!r} is not the unit's {want!r}")
    if (m["kind"] == "qpu") != (m["backend"] in q.fixer.IBM_DEVICES):
        out.append("kind: a qpu bundle names an IBM device, and only a qpu bundle does")
    options = {k: dict(v) if isinstance(v, dict) else v for k, v in m["options"].items()}
    delay = options.get("execution", {}).pop("rep_delay", None) if isinstance(options.get("execution"), dict) else None
    if not q.bundle.same_json(options, U.OPTIONS) or not (delay is None or (type(delay) in (int, float) and delay > 0)):
        out.append(f"options: {m['options']!r} are not the recipe's {U.OPTIONS} (rep_delay aside)")
    if m["options_sha256"] != q.fixer.options_digest(m["options"]):
        out.append("options_sha256: not the digest of the options the manifest states")
    if m["known_answer"] != list(U.KNOWN_ANSWER) or m["pair"] != list(U.PAIR):
        out.append("known_answer or pair: not the recipe's")
    if m["source"] != {"path": U.SOURCE_PATH, "sha256": U.SOURCE_SHA256}:
        out.append("source: not the shipped circuit ed767c01bd4b851d")
    block = m["unit"]
    for term, want in (("recipe", U.RECIPE_NAME), ("recipe_sha256", U.recipe_sha256(divisor)), ("shots_divisor", divisor),
                       ("device_order", list(U.DEVICE_SETS[kind]))):
        if not isinstance(block, dict) or block.get(term) != want:
            out.append(f"unit.{term}: not {want!r}")
    t = m["target"]
    if not (isinstance(t, dict) and set(t) == {"name", "num_qubits", "calibration", "coupling"} and t["name"] == m["backend"]):
        out.append("target: {name (the backend), num_qubits, calibration, coupling}")
    if not q.bundle.is_utc(m["frozen_at"]):
        out.append("frozen_at: a UTC time")
    return out


def _jobs_problems(q, m, divisor):
    planned = U.jobs_of_device(divisor)
    js = m["jobs"]
    if not (isinstance(js, list) and [j.get("job") if isinstance(j, dict) else None for j in js] == [p[0] for p in planned]):
        return [f"jobs: the unit's six jobs in order, {[p[0] for p in planned]}"]
    out = []
    for j, (name, k, _p, pubs) in zip(js, planned, strict=True):
        if set(j) != {"job", "max_execution_time", "circuits"}:
            out.append(f"jobs.{name}: fields {sorted(j)}")
            continue
        if j["max_execution_time"] != U.CAPS[k]:
            out.append(f"jobs.{name}: max_execution_time {j['max_execution_time']!r} is not the recipe's {U.CAPS[k]}")
        cs = j["circuits"]
        if not (isinstance(cs, list) and len(cs) == len(pubs) and all(isinstance(e, dict) for e in cs)):
            out.append(f"jobs.{name}: {len(pubs)} circuits, in PUB order")
            continue
        for e, (pub, cname, role, basis, shots) in zip(cs, pubs, strict=True):
            if (e.get("pub"), e.get("name"), e.get("role"), e.get("basis"), e.get("shots")) != (pub, cname, role, basis, shots):
                out.append(f"jobs.{name}[{pub}]: pub, name, role, basis and shots are not the recipe's")
            elif sorted(e) != sorted(q.bundle.ENTRY):
                out.append(f"jobs.{name}[{pub}]: fields {sorted(e)}")
    return out
