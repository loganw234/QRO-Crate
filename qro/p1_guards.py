"""P1's guards, as functions any generator of a crate of Quantum-Film's records may call (P1.3; the lead's ruling of
2026-11-08T15:33:03Z): G2's line half, G3, G4 and G5, G6, G7, G8 and G9, and the one place every guard of P1's generators
raises (`hold`). qro/p1_generate.py calls them, and so may P5's unit generator, which holds a unit's records to the same
rules: each rule has one place.

What this module is not. It imports the standard library and P1's readers (p1_records, p1_forms, p1_decode, p1_commit)
and nothing else: not qro.p1_generate, not any module of P2's, no register module (a test reads its imports). It knows no
layout of Quantum-Film's tree, no device name and no directory of the read of 2026-10-14: every path a guard names is an
argument, and the only path a guard holds a record to (G8's `committed_path`) is the caller's.

The one switch. Every guard raise of P1's generators goes through `hold`, and every reader's refusal through
`read_record`, both looked up on this module when they are called, so that one monkeypatch of `p1_guards.hold` switches
every guard, G1 to G12, off (the sentinel test, T2).

The arguments the guards take.
  crate   anything with `read(rel) -> bytes` and `info(rel) -> (the file's SHA-256, its size)`; `hold_read_manifest` also
          reads `crate.paths`, the sorted paths of the crate's files. P1's `Crate` is one.
  files   {"line", "raw", "metrics", "submitting": the path of each in the crate}; they name the place in a raise, and
          `hold_line` reads the submitting marker at its path.
  job     anything with the attributes `device`, `id`, `spec`, `line`, `first` and `metrics`. P1's `Job` is one.
  spec, manifest, line, records, raw, metrics   what P1's readers return (p1_records, p1_forms).
The guards a function holds are in its docstring; `EXPORTS` lists the names P5 may import, and tests/p1/test_p1_exports.py
pins each name and signature."""
from qro import p1_commit, p1_decode, p1_forms, p1_records as rec

MAX_PUBS = 10                        # a Pub's id ends in one decimal digit of its index (step 4)

EXPORTS = ("GuardError", "hold", "read_record", "hold_line", "hold_device_runs", "hold_commitments_and_counts",
           "hold_metrics", "hold_refetch_job", "hold_refetch_result", "hold_read_manifest", "MAX_PUBS")


class GuardError(ValueError):
    """A record that disagrees with another, or a file that fits no layout: the guard, the place and the reason."""

    def __init__(self, guard, where, detail):
        super().__init__(f"{guard} at {where}: {detail}")
        self.guard, self.where, self.detail = guard, where, detail


def hold(ok, guard, where, detail):
    """Every guard of the generators: the one place a test switches them off (T2). A GuardError of `guard` unless `ok`."""
    if not ok:
        raise GuardError(guard, where, detail)


def read_record(guard, where, fn, *args):
    """A reader of p1_records, p1_forms or p1_decode, its refusal a raise of `guard`: a decode rule that cannot read the
    bytes it is told to is a verdict on the records, as a record that is not in its format is."""
    try:
        return fn(*args)
    except (rec.RecordError, p1_forms.RawFormError, p1_forms.SnapshotError, p1_decode.DecodeError) as x:
        raise GuardError(guard, where, str(x)) from None


def hold_line(crate, name, files, manifest, mdigest, spec, line):
    """G2, the line's half: the job's line holds its manifest's bundle digest, its commitments in PUB order, and its
    manifest's stock, kind, route, backend and program; its submitting marker names the job `name` and the bundle."""
    path = files["line"]
    hold(line.bundle_sha256 == mdigest, "G2", path, "the line's bundle_sha256 is not the manifest's SHA-256")
    hold(line.commitments == tuple(c.commitment for c in spec), "G2", path,
         "the line's commitments are not the manifest job's, in PUB order")
    for term in ("stock", "kind", "route", "backend", "program"):
        hold(getattr(line, term) == getattr(manifest, term), "G2", path, f"the line's {term} is not the manifest's")
    marker = read_record("G2", files["submitting"], rec.parse, crate.read(files["submitting"]), files["submitting"])
    hold(marker.get("job") == name and marker.get("bundle_sha256") == mdigest, "G2", files["submitting"],
         "the submitting marker does not name this job and its bundle")


def hold_device_runs(crate, where, found, manifest, spec, line):
    """G3: the job's device-run records, one for each PUB: {k: (path, DeviceRun, Circuit)}. `found` is {k: [(path,
    circuit name)]}. At most MAX_PUBS PUBs; a record for each and none for two; each record's digest is the SHA-256 of
    its body, and its source and role agree with the manifest entry and the line."""
    hold(len(spec) <= MAX_PUBS, "G3", where,
         f"the job has {len(spec)} PUBs; a PUB index is one decimal digit of its id, and an eleventh needs a new rule")
    hold(sorted(found) == list(range(len(spec))), "G3", where,
         f"the records are of PUBs {sorted(found)}; the job has {len(spec)}")
    out = {}
    for k, held in sorted(found.items()):
        hold(len(held) == 1, "G3", where, f"PUB {k} has {len(held)} records")
        path, circuit_name = held[0]
        c = spec[k]
        hold(circuit_name == c.name, "G3", path, f"the record is of circuit {circuit_name}; the manifest's PUB {k} is {c.name}")
        run = read_record("G3", path, rec.device_run, crate.read(path), path)
        hold(run.digest == rec.record_digest(run.doc), "G3", path, "the record's digest is not the SHA-256 of its body")
        s = run.source
        for term, want in (("job_id", line.job_id), ("submitted_at", line.submitted_at), ("backend", manifest.backend),
                           ("kind", manifest.kind), ("program", manifest.program), ("route", manifest.route),
                           ("decode", manifest.decode), ("options", manifest.options),
                           ("options_sha256", manifest.options_sha256), ("pub", k), ("shots", c.shots),
                           ("circuit_sha256", c.circuit_sha256), ("isa_sha256", c.isa_sha256),
                           ("commitment", c.commitment), ("salt", c.salt)):
            hold(term in s and s[term] == want and type(s[term]) is type(want), "G3", path,
                 f"the record's source.{term} is not the manifest's or the line's")
        for term, have, want in (("stock", run.stock, manifest.stock), ("role", run.role, c.role),
                                 ("basis", run.basis, c.basis)):
            hold(have == want, "G3", path, f"the record's {term} is not the manifest's")
        out[k] = (path, run, c)
    return out


def hold_commitments_and_counts(files, manifest, spec, line, records, raw):
    """G4 and G5: each PUB's commitment, the manifest's, the line's, the record's and IBM's echo inside the raw bytes, is
    the one the record's fourteen inputs recompute to (G4); the raw result holds a PUB for each commitment of the line,
    with the manifest's shots, and the counts of the decode under the manifest's rule and order are the record's,
    exactly (G5). `records` is hold_device_runs' answer."""
    rule = p1_decode.RULES.get(manifest.decode)
    hold(rule is not None, "G5", files["raw"], f"no decode rule {manifest.decode} is built")
    hold(len(raw.pubs) == len(spec) == len(line.commitments), "G5", files["raw"],
         f"the raw result holds {len(raw.pubs)} PUBs; the line lists {len(line.commitments)} and the manifest {len(spec)}")
    for k, (path, run, c) in records.items():
        want = p1_commit.commitment_of(read_record("G4", path, run.fields, path))
        for name, have in (("the manifest's", c.commitment), ("the line's", line.commitments[k]),
                           ("the record's", run.source.get("commitment")), ("IBM's echo", raw.pubs[k].echo)):
            hold(have == want, "G4", path, f"{name} commitment is not the one the record's inputs recompute to")
        hold(raw.pubs[k].rows == c.shots, "G5", files["raw"],
             f"PUB {k} holds {raw.pubs[k].rows} rows; the manifest says {c.shots} shots")
        counts = read_record("G5", path, p1_decode.ibm_counts, raw.pubs[k], rule.order)
        hold(counts == run.counts, "G5", path,
             "the record's counts are not the raw result's, decoded under the manifest's rule")


def hold_metrics(files, line, metrics, raw):
    """G6: the metrics wrapper names the line's job and device, holds the line's submitted time as IBM's created time,
    and the raw result's execution span, where it has one, lies in [running, finished]."""
    path = files["metrics"]
    hold(metrics.job_id == line.job_id and metrics.backend == line.backend, "G6", path,
         "the metrics wrapper names another job or device than the line")
    submitted = read_record("G6", path, rec.instant, line.submitted_at, f"{files['line']} submitted_at")
    hold(metrics.created == submitted, "G6", path, "IBM's created time is not the line's submitted time")
    if raw.spans:
        hold(metrics.running <= raw.first_shot and raw.last_shot <= metrics.finished, "G6", path,
             "the execution span is not inside [running, finished]")


def hold_refetch_job(crate, path, job):
    """G7: the read's job record at `path`, returned: of the job's device and id and its role, its three flags hold, IBM's
    copy, the line and the read hold the same PUBs and commitments, its first shot is the span's start (where the raw
    result has one) and its running time is the metrics'."""
    r = read_record("G7", path, rec.refetch_job, crate.read(path), path)
    hold((r.device, r.job_id) == (job.device, job.id), "G7", path, "the record is of another job or device")
    hold({c.role for c in job.spec} == {r.role}, "G7", path, "the record's role is not the job's")
    for flag in ("commitments_equal", "created_equal_to_line", "options_equal_to_manifest"):
        hold(r.holds.get(flag) is True, "G7", path, f"the read's flag {flag} does not hold")
    hold(r.pubs_in_ibm_copy == r.pubs_in_line == len(job.line.commitments) == len(r.pubs), "G7", path,
         "IBM's copy, the line and the read do not hold the same PUBs")
    for k, p in enumerate(r.pubs):
        hold(p.get("gate_list_equal") is True and p.get("gates_equal") is True, "G7", path,
             f"the read's gate-list flags do not hold for PUB {k}")
        hold(p.get("commitment_in_ibm_copy") == p.get("commitment_in_line") == job.line.commitments[k], "G7", path,
             f"the read's commitments for PUB {k} are not the line's")
    if job.first is not None:
        hold(r.first_shot == job.first, "G7", path, "the read's first shot is not the execution span's start")
    hold(r.running == job.metrics.running, "G7", path, "the read's running time is not the metrics'")
    return r


def hold_refetch_result(crate, path, job, raw_path, committed_path):
    """G8: the read's result record at `path`, returned: of the job's device and id, it says IBM's copy is the same
    bytes, its digests and sizes are those of the raw result at `raw_path` in the crate, and it names `committed_path`
    as the file it committed (the caller's: Quantum-Film's tree names `docs/records/` and the raw path)."""
    r = read_record("G8", path, rec.refetch_result, crate.read(path), path)
    digest, size = crate.info(raw_path)
    hold((r.device, r.job_id) == (job.device, job.id), "G8", path, "the record is of another job or device")
    hold(r.bytes_equal and r.agree_at == "bytes", "G8", path, "the read does not say IBM's copy is the same bytes")
    hold(r.committed_sha256 == r.ibm_sha256 == digest and r.committed_bytes == r.ibm_bytes == size, "G8", path,
         "the record's digests and sizes are not the raw result's")
    hold(r.committed_path == committed_path, "G8", path, "the record names another file than the raw result")
    return r


def hold_read_manifest(crate, held, root, expect, carried, snapshot):
    """G9: one MANIFEST of the read, whose files lie under `root` (a prefix ending in `/`) in the crate: {file name under
    root: (size, SHA-256)} as it lists them, or None for a directory with no files and no MANIFEST. `held` is the paths
    the crate classified as this MANIFEST, `expect` its format. At most one MANIFEST; wherever the directory holds files
    it holds its MANIFEST; the MANIFEST lists each file of the directory as it hashes and each file it lists of the
    directory is the file's; every snapshot it lists (a name `snapshot`, a compiled pattern with a `device` group,
    matches) of a device in `carried` is in the crate."""
    hold(len(held) <= 1, "G9", root, "more than one MANIFEST")
    hold(bool(held) or not any(rel.startswith(root) for rel in crate.paths), "G9", root,
         "the read's directory holds files and not its MANIFEST, which lists them")
    if not held:
        return None
    listed = read_record("G9", held[0], rec.read_manifest, crate.read(held[0]), held[0], expect)
    for rel in crate.paths:
        if rel.startswith(root) and rel != held[0]:
            name = rel[len(root):]
            hold(name in listed, "G9", rel, "this file is in the read's directory and not in its MANIFEST")
            hold((crate.info(rel)[1], crate.info(rel)[0]) == listed[name], "G9", rel,
                 "this file is not the size and SHA-256 its MANIFEST lists")
    for name in sorted(listed):               # a snapshot the read lists of a device the crate carries is carried
        m = snapshot.fullmatch(name)
        if m and m.group("device") in carried:
            hold(root + name in crate.paths, "G9", held[0],
                 f"the MANIFEST lists {name}, a snapshot of {m.group('device')}, which the crate carries jobs of, "
                 "and the crate lacks it")
    return listed
