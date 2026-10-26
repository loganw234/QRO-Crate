"""P1's raw forms and its snapshot form: a file's bytes in, the parsed document out, or a refusal to read them
(P1's design, item 2; P1.1). Standard library only, and `qro.checker` for its `RawFormError`.

Three raw forms, each read by one function, and one form that is not a raw result:
  - `ibm-sampler-result/v1`: IBM's SamplerV2 result text, runtime 0.50.0's RuntimeEncoder JSON, as IBM returned it.
    Per PUB a `.npy` v1.0 array of shape (rows, 2), unsigned bytes, deflated and then base64'd; per PUB the
    commitment IBM echoed; per job its execution span. A row is one shot: two bytes, a 16-bit outcome, big-endian.
  - `atlas-tomography-result/v1`: Quantum-Film's wrapper of Moth's tomography response: counts per setting, not
    shots in order, with the engine's own observables beside them. Where Quantum-Film recorded when it fetched the
    result, a top-level `fetched_at`, a time in the profile's one spelling, is admitted and read for nothing: five of
    the six real law results (2026-09-26) carry it, and the one of 2026-09-25 does not.
  - `atlas-known-answer-vector/v1`: Quantum-Film's frozen known-answer vector: `{job, measurements}`.
  - a calibration snapshot: IBM's backend properties text, not a raw result (it has no shots), read by
    `parse_snapshot` and refused as a `SnapshotError`.

A reader refuses by raising `RawFormError` (the checker's own), with the place and the reason in its text; it
raises nothing else on any bytes: a hostile file is a refusal, never a crash (FORMAT.md, item 16). Every parse is
strict JSON: UTF-8, no key twice in one object, no NaN, no infinity, no float that overflows binary64 (`1e999` is
refused; one that underflows, `1e-999`, is read as 0.0, in every reader), and no integer past 2^63 - 1 (the profile's
own bound for an `integer`, qro.spelling.MAX, on either side of zero). What a reader will
decompress is capped at CAP bytes in all, and at what the array's own header declares. What it returns is
what the bytes hold: the shots a form counts are never a number stated beside the bytes (rule 7).

The shots of each form (the number step 3 holds `qro:shots` to):
  - IBM: the rows of each PUB, which must all be equal. A job's PUBs share one shot count: Quantum-Film's bundle
    check and runtime 0.50.0 both say so.
  - Atlas: the shots per setting, which every setting of one result must share. Atlas returns counts per setting,
    and each setting is its own run of that many shots on the engine.
"""
import base64
import binascii
import json
import math
import re
import zlib
from dataclasses import dataclass
from datetime import datetime, timezone

from qro import spelling
from qro.checker import RawFormError

CAP = 64 * 1024 * 1024        # the most bytes any reader decompresses for one result, whatever its headers declare
IBM_BITS = 16                 # a v0 result is 16 classical bits wide: two bytes a shot


class SnapshotError(ValueError):
    """The bytes are not a calibration snapshot in the closed form below."""


class _Twice(Exception):
    """A key twice in one object, a NaN or infinity, a float that overflows binary64, or an integer past 2^63 - 1."""


def _pairs(pairs):
    out = {}
    for k, v in pairs:
        if k in out:
            raise _Twice(f"the key {k!r} twice in one object")
        out[k] = v
    return out


def _constant(name):
    raise _Twice(f"{name} has no value")


def _float(text):
    x = float(text)
    if math.isinf(x):                         # 1e999 reads as infinity, and calls no constant hook
        raise _Twice(f"{text} is past binary64")
    return x                                  # 1e-999 reads as 0.0: only an overflow is past binary64


def _integer(text):
    """The integer a numeral says, held before it is converted: a JSON numeral has no leading zero, so one of more than
    nineteen digits is past 2^63 - 1 whatever its digits are, and is never converted (Python converts no more than
    4,300 digits unless the host lifts the limit)."""
    n = int(text) if len(text.lstrip("-")) <= 19 else None
    if n is None or not -spelling.MAX <= n <= spelling.MAX:
        raise _Twice(f"{text[:24]}{'...' if len(text) > 24 else ''} is an integer past {spelling.MAX}")
    return n


def load_json(data, what, error=RawFormError):
    """`data` as strict JSON, or `error`: UTF-8, no key twice, no NaN or infinity, no float that overflows binary64 (one
    that underflows, `1e-999`, is read as 0.0), no integer past 2^63 - 1 (on either side of zero), and nothing nested
    deeper than the parser reads."""
    try:
        return json.loads(data.decode("utf-8"), object_pairs_hook=_pairs, parse_constant=_constant,
                          parse_float=_float, parse_int=_integer)
    except _Twice as x:
        raise error(f"{what}: {x}") from None
    except UnicodeDecodeError:
        raise error(f"{what}: not UTF-8") from None
    except json.JSONDecodeError as x:
        raise error(f"{what}: not JSON ({x.msg}, line {x.lineno} column {x.colno})") from None
    except RecursionError:
        raise error(f"{what}: nested deeper than the reader reads") from None
    except ValueError as x:                   # what the parser will not convert (none is known: an integer is held first)
        raise error(f"{what}: not readable ({x})") from None


# -- times -----------------------------------------------------------------------------------------------------
_STAMP = re.compile(r"([0-9]{4})-([0-9]{2})-([0-9]{2})T([0-9]{2}):([0-9]{2}):([0-9]{2})(?:\.([0-9]{1,6}))?", re.ASCII)


def parse_time(text, zone="Z"):
    """An aware datetime in UTC from YYYY-MM-DDTHH:MM:SS, then a fraction of one to six digits (trailing zeros
    allowed: IBM writes six), then `zone`: "Z" for the profile's own spelling, or "" for IBM's execution spans,
    which are zone-less and read as UTC (study QRO-0, section 4.4). A real time: no leap second's :60. ValueError
    for anything else."""
    if not isinstance(text, str) or zone not in ("Z", ""):
        raise ValueError("not a time")
    if zone and not text.endswith(zone):
        raise ValueError(f"{text!r}: a time in UTC ends in Z")
    m = _STAMP.fullmatch(text[:len(text) - len(zone)])
    if not m:
        raise ValueError(f"{text!r}: not YYYY-MM-DDTHH:MM:SS with a fraction of one to six digits")
    y, mo, d, h, mi, s = (int(m.group(i)) for i in range(1, 7))
    micro = int((m.group(7) or "").ljust(6, "0"))
    try:
        return datetime(y, mo, d, h, mi, s, micro, tzinfo=timezone.utc)
    except ValueError:
        raise ValueError(f"{text!r}: not a real time") from None


# -- the shapes JSON documents are held to ----------------------------------------------------------------------
def _object(x, where, required, allowed=None, error=RawFormError):
    """`x` as an object holding every key of `required` and no key outside `allowed` (default: just those)."""
    allowed = required if allowed is None else allowed
    if not isinstance(x, dict):
        raise error(f"{where}: not an object")
    missing = sorted(required - set(x))
    extra = sorted(set(x) - allowed)
    if missing or extra:
        raise error(f"{where}: " + "; ".join(([f"lacks {missing}"] if missing else [])
                                             + ([f"holds {extra}, which the form does not"] if extra else [])))
    return x


def _typed(x, name, where):
    """The value of IBM's RuntimeEncoder wrapper {"__type__": name, "__value__": ...}, and nothing else in it."""
    _object(x, where, {"__type__", "__value__"})
    if x["__type__"] != name:
        raise RawFormError(f"{where}: not a {name}")
    return x["__value__"]


def _whole(x):
    """A JSON integer, which a bool is not."""
    return type(x) is int


# -- IBM's sampler result ----------------------------------------------------------------------------------------
_NPY_MAGIC = b"\x93NUMPY\x01\x00"
_NPY_HEADER = re.compile(rb"\{'descr': '\|u1', 'fortran_order': False, 'shape': \((0|[1-9][0-9]*), 2\), \} *\n")


@dataclass(frozen=True)
class IbmPub:
    rows: int                 # the shots this PUB holds
    body: bytes               # rows x 2 bytes: one 16-bit outcome a shot, big-endian
    echo: str | None          # the commitment IBM echoed for this PUB (metadata.circuit_metadata.qf_commitment)


@dataclass(frozen=True)
class IbmResult:
    pubs: tuple               # of IbmPub, in the order IBM returned them
    spans: tuple              # of (start, stop), aware UTC datetimes: the job's execution spans; () where it has none
    shots: int                # the rows each PUB holds, which are all equal

    @property
    def first_shot(self):
        return min(s[0] for s in self.spans) if self.spans else None

    @property
    def last_shot(self):
        return max(s[1] for s in self.spans) if self.spans else None


def _array(text, where, budget):
    """The rows and the bytes of one PUB's array: base64 of zlib of a `.npy` v1.0 file of unsigned bytes, shape
    (rows, 2), C order. What it will inflate is the header's rows x 2 and the header, nothing more."""
    try:
        blob = base64.b64decode(text.encode("ascii"), validate=True)
    except (UnicodeEncodeError, binascii.Error, ValueError):
        raise RawFormError(f"{where}: not base64") from None
    inflate = zlib.decompressobj()
    try:
        head = inflate.decompress(blob, 256)
    except zlib.error:
        raise RawFormError(f"{where}: not a zlib stream") from None
    if len(head) < 10 or head[:8] != _NPY_MAGIC:
        raise RawFormError(f"{where}: not a .npy v1.0 array")
    size = int.from_bytes(head[8:10], "little")
    m = _NPY_HEADER.fullmatch(head[10:10 + size]) if 10 + size <= len(head) else None
    if not m:
        raise RawFormError(f"{where}: a .npy header that is not unsigned bytes of shape (rows, 2) in C order")
    rows = int(m.group(1))
    want = 10 + size + 2 * rows
    if rows < 1 or want > CAP or 2 * rows > budget[0]:
        raise RawFormError(f"{where}: {rows} rows, which is none, or more than the reader inflates")
    if len(head) > want:
        raise RawFormError(f"{where}: the array holds more bytes than its header declares")
    try:
        out = head + inflate.decompress(inflate.unconsumed_tail, want - len(head) + 1)
    except zlib.error:
        raise RawFormError(f"{where}: not a zlib stream") from None
    if len(out) != want:
        raise RawFormError(f"{where}: the array holds {len(out) - 10 - size} bytes, not the {2 * rows} its header "
                           "declares")
    if not inflate.eof or inflate.unused_data or inflate.unconsumed_tail:
        raise RawFormError(f"{where}: the zlib stream does not end where the array does")
    budget[0] -= 2 * rows
    return rows, bytes(out[10 + size:])


def _echo(meta, where):
    if meta is None:
        return None
    if not isinstance(meta, dict):
        raise RawFormError(f"{where}.metadata: not an object")
    if "circuit_metadata" not in meta:
        return None
    circuit = meta["circuit_metadata"]
    if not isinstance(circuit, dict):
        raise RawFormError(f"{where}.metadata.circuit_metadata: not an object")
    if "qf_commitment" not in circuit:
        return None
    if not isinstance(circuit["qf_commitment"], str):
        raise RawFormError(f"{where}.metadata.circuit_metadata.qf_commitment: not a string")
    return circuit["qf_commitment"]


def _ibm_pub(x, where, budget):
    value = _object(_typed(x, "SamplerPubResult", where), where, {"data"}, {"data", "metadata"})
    dbin = _object(_typed(value["data"], "DataBin", f"{where}.data"), f"{where}.data",
                   {"field_names", "shape", "fields"}, {"field_names", "field_types", "shape", "fields"})
    if dbin["field_names"] != ["meas"] or dbin["shape"] != [] or not isinstance(dbin["fields"], dict) \
            or list(dbin["fields"]) != ["meas"]:
        raise RawFormError(f"{where}.data: not one field, meas, of shape []")
    bits = _object(_typed(dbin["fields"]["meas"], "BitArray", f"{where}.data.meas"), f"{where}.data.meas",
                   {"array", "num_bits"})
    if not _whole(bits["num_bits"]) or bits["num_bits"] != IBM_BITS:
        raise RawFormError(f"{where}.data.meas: not {IBM_BITS} bits")
    text = _typed(bits["array"], "ndarray", f"{where}.data.meas.array")
    if not isinstance(text, str):
        raise RawFormError(f"{where}.data.meas.array: not a string")
    rows, body = _array(text, f"{where}.data.meas.array", budget)
    return IbmPub(rows, body, _echo(value.get("metadata"), where))


def _spans(meta):
    if meta is None:
        return ()
    if not isinstance(meta, dict):
        raise RawFormError("the result's metadata: not an object")
    if "execution" not in meta:
        return ()
    execution = meta["execution"]
    if not isinstance(execution, dict):
        raise RawFormError("metadata.execution: not an object")
    if "execution_spans" not in execution:
        return ()
    listed = _object(_typed(execution["execution_spans"], "ExecutionSpans", "metadata.execution.execution_spans"),
                     "metadata.execution.execution_spans", {"spans"})["spans"]
    if not isinstance(listed, list) or not listed:
        raise RawFormError("execution_spans: a list of one span or more")
    out = []
    for i, s in enumerate(listed):
        where = f"execution_spans.spans[{i}]"
        v = _object(_typed(s, "DoubleSliceSpan", where), where, {"start", "stop"}, {"start", "stop", "data_slices"})
        try:
            start = parse_time(_typed(v["start"], "datetime", f"{where}.start"), "")
            stop = parse_time(_typed(v["stop"], "datetime", f"{where}.stop"), "")
        except ValueError as x:
            raise RawFormError(f"{where}: {x}") from None
        if stop < start:
            raise RawFormError(f"{where}: stops before it starts")
        out.append((start, stop))
    return tuple(out)


def parse_ibm_result(data):
    """An IbmResult from IBM's result text, or RawFormError."""
    top = _typed(load_json(data, "the result"), "PrimitiveResult", "the result")
    value = _object(top, "the result", {"pub_results"}, {"pub_results", "metadata"})
    results = value["pub_results"]
    if not isinstance(results, list) or not results:
        raise RawFormError("pub_results: a list of one PUB or more")
    budget = [CAP]
    pubs = tuple(_ibm_pub(r, f"pub_results[{i}]", budget) for i, r in enumerate(results))
    if len({p.rows for p in pubs}) != 1:
        raise RawFormError("pub_results: PUBs of different row counts; a job's PUBs share one shot count")
    return IbmResult(pubs, _spans(value.get("metadata")), pubs[0].rows)


# -- Atlas's tomography result and the frozen known-answer vector ------------------------------------------------
_LABEL = re.compile(r"[IXYZ]{16}", re.ASCII)
_OUTCOME = re.compile(r"[01]{16}", re.ASCII)


@dataclass(frozen=True)
class AtlasSetting:
    shots: int
    counts: dict              # {a 16-character string of 0 and 1: the shots that read it}


@dataclass(frozen=True)
class AtlasResult:
    job: str
    settings: dict            # {label: AtlasSetting}, in the file's order
    observables: dict | None  # the engine's own, as it wrote them; None for the vector
    shots: int                # the shots per setting, which every setting shares
    spans = ()                # Atlas reports no execution span: a result in this form has no first shot
    first_shot = None
    last_shot = None


def _settings(measurements):
    if not isinstance(measurements, dict) or not measurements:
        raise RawFormError("measurements: an object of one setting or more")
    out, shots = {}, set()
    for label, m in measurements.items():
        where = f"measurements[{label!r}]"
        if not _LABEL.fullmatch(label):
            raise RawFormError(f"{where}: a label is 16 characters of I, X, Y and Z")
        _object(m, where, {"counts", "shots"})
        if not _whole(m["shots"]) or m["shots"] < 1:
            raise RawFormError(f"{where}: shots is a whole number of one or more")
        counts = m["counts"]
        if not isinstance(counts, dict) or not counts:
            raise RawFormError(f"{where}: counts is an object of one outcome or more")
        for s, c in counts.items():
            if not _OUTCOME.fullmatch(s) or not _whole(c) or c < 1:
                raise RawFormError(f"{where}: a count is a whole number of one or more, of a 16-character string of "
                                   "0 and 1")
        if sum(counts.values()) != m["shots"]:
            raise RawFormError(f"{where}: counts that do not sum to its shots")
        shots.add(m["shots"])
        out[label] = AtlasSetting(m["shots"], counts)
    if len(shots) != 1:
        raise RawFormError("measurements: settings that disagree on their shots")
    return out, shots.pop()


_ATLAS_TOP = {"job_id", "path", "response", "status", "taken_from"}


def parse_atlas_result(data):
    """An AtlasResult from Quantum-Film's wrapper of the engine's response, or RawFormError. The wrapper may carry
    a top-level `fetched_at`, which is held to the profile's spelling of a time and read for nothing."""
    top = _object(load_json(data, "the result"), "the result", _ATLAS_TOP, _ATLAS_TOP | {"fetched_at"})
    if not isinstance(top["job_id"], str) or not isinstance(top["path"], str) \
            or not isinstance(top["taken_from"], str) or not _whole(top["status"]):
        raise RawFormError("the result: job_id, path and taken_from are strings, status a whole number")
    if "fetched_at" in top:
        fetched = top["fetched_at"]
        problem = "not a string" if not isinstance(fetched, str) else spelling.problem("time", fetched)
        if problem:
            raise RawFormError(f"the result: fetched_at is not a time in the profile's spelling ({problem})")
    result = _object(_object(top["response"], "response", {"result"})["result"], "response.result",
                     {"measurements", "observables", "density_matrices"})
    if not isinstance(result["observables"], dict) or not isinstance(result["density_matrices"], dict):
        raise RawFormError("response.result: observables and density_matrices are objects")
    settings, shots = _settings(result["measurements"])
    return AtlasResult(top["job_id"], settings, result["observables"], shots)


def parse_atlas_vector(data):
    """An AtlasResult (with no observables) from Quantum-Film's frozen known-answer vector, or RawFormError."""
    top = _object(load_json(data, "the vector"), "the vector", {"job", "measurements"})
    if not isinstance(top["job"], str):
        raise RawFormError("the vector: job is a string")
    settings, shots = _settings(top["measurements"])
    return AtlasResult(top["job"], settings, None, shots)


# -- the forms, by the name a raw result carries ------------------------------------------------------------------
PARSERS = {"ibm-sampler-result/v1": parse_ibm_result, "atlas-tomography-result/v1": parse_atlas_result,
           "atlas-known-answer-vector/v1": parse_atlas_vector}


def parse_raw(form, data):
    """The parsed raw result of the named form: KeyError for a form this module does not read."""
    return PARSERS[form](data)


def read_ibm(data):
    return parse_ibm_result(data).shots


def read_atlas_result(data):
    return parse_atlas_result(data).shots


def read_atlas_vector(data):
    return parse_atlas_vector(data).shots


READERS = {"ibm-sampler-result/v1": read_ibm, "atlas-tomography-result/v1": read_atlas_result,
           "atlas-known-answer-vector/v1": read_atlas_vector}


# -- a calibration snapshot: IBM's backend properties, not a raw result ----------------------------------------------
@dataclass(frozen=True)
class Snapshot:
    device: str               # backend_name
    stamp: datetime           # last_update_date: the snapshot's own stamp
    newest: datetime          # the newest `date` anywhere inside: the newest measurement the snapshot holds
    doc: dict                 # the parsed document, which values_digest reads


def _snapshot_time(x, where):
    try:
        return parse_time(x, "Z")
    except ValueError as err:
        raise SnapshotError(f"{where}: {err}") from None


def _exact_number(x, where):
    """A number that is not a bool, and an integer only if binary64 holds it exactly (2^53 + 1 is the first it does
    not). The reader's own bound, 2^63 - 1, is met first for anything past it, so an integer too big for `float` does
    not reach here by `parse_snapshot`; the OverflowError is caught for a caller that hands the helper one."""
    if type(x) not in (int, float):
        raise SnapshotError(f"{where}: not a number")
    if type(x) is int:
        try:
            exact = int(float(x)) == x
        except OverflowError:
            exact = False
        if not exact:
            raise SnapshotError(f"{where}: an integer binary64 cannot hold")


def _text(x, where):
    if not isinstance(x, str):
        raise SnapshotError(f"{where}: not a string")


def _qubits(x, where):
    if not isinstance(x, list):
        raise SnapshotError(f"{where}: not a list")
    for i, q in enumerate(x):
        if not _whole(q):
            raise SnapshotError(f"{where}[{i}]: not a whole number")
        _exact_number(q, f"{where}[{i}]")


def _measured(x, where, dates):
    _object(x, where, {"date", "name", "unit", "value"}, error=SnapshotError)
    dates.append(_snapshot_time(x["date"], f"{where}.date"))
    _text(x["name"], f"{where}.name")
    _text(x["unit"], f"{where}.unit")
    _exact_number(x["value"], f"{where}.value")


def _listed(x, where):
    if not isinstance(x, list):
        raise SnapshotError(f"{where}: not a list")
    return x


def parse_snapshot(data):
    """A Snapshot from IBM's backend properties text, or SnapshotError. The form is closed: exactly the keys
    backend_name, backend_version, gates, general, general_qlists, last_update_date and qubits; each entry of the
    shapes the vocabulary of IBM's properties gives it; every date `YYYY-MM-DDTHH:MM:SS[.f]Z`; every value a
    number that is not a bool, NaN or infinity, and every integer one binary64 holds exactly. Anything else is not
    a snapshot, so a field outside the schema is refused, never ignored."""
    doc = load_json(data, "the snapshot", SnapshotError)
    _object(doc, "the snapshot", {"backend_name", "backend_version", "gates", "general", "general_qlists",
                                  "last_update_date", "qubits"}, error=SnapshotError)
    _text(doc["backend_name"], "backend_name")
    _text(doc["backend_version"], "backend_version")
    stamp = _snapshot_time(doc["last_update_date"], "last_update_date")
    dates = []
    for i, g in enumerate(_listed(doc["gates"], "gates")):
        where = f"gates[{i}]"
        _object(g, where, {"gate", "name", "parameters", "qubits"}, error=SnapshotError)
        _text(g["gate"], f"{where}.gate")
        _text(g["name"], f"{where}.name")
        _qubits(g["qubits"], f"{where}.qubits")
        for j, p in enumerate(_listed(g["parameters"], f"{where}.parameters")):
            _measured(p, f"{where}.parameters[{j}]", dates)
    for i, g in enumerate(_listed(doc["general"], "general")):
        _measured(g, f"general[{i}]", dates)
    for i, g in enumerate(_listed(doc["general_qlists"], "general_qlists")):
        where = f"general_qlists[{i}]"
        _object(g, where, {"name", "qubits"}, error=SnapshotError)
        _text(g["name"], f"{where}.name")
        _qubits(g["qubits"], f"{where}.qubits")
    for i, row in enumerate(_listed(doc["qubits"], "qubits")):
        for j, q in enumerate(_listed(row, f"qubits[{i}]")):
            _measured(q, f"qubits[{i}][{j}]", dates)
    if not dates:
        raise SnapshotError("the snapshot holds no measurement date, so it has no newest value")
    return Snapshot(doc["backend_name"], stamp, max(dates), doc)
