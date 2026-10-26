"""The entity graph as P1's steps and P2's step 6 read it (P1's design, items 1.1 and 8; P1.1). Standard library only.

An Index is built from metadata that has an "@graph": the checker's parsed metadata, or `{"@graph": [entities]}`
built by a generator while a crate is being made, when no metadata file exists yet (P2's design, found 2; the
lead's decision 10). It reads nothing else of the metadata, so both work alike, and it asks nothing of the file
system. It is a snapshot of the graph it was built from, not a view of it. At construction it walks the graph once and
builds `by_id` (a plain dict of the entities themselves, which a caller may change) and the lookup of entities by type.
A metadata with no list `@graph`, an entity that is no object or has no string @id, an @id twice, and an `@type` that is a
list holding something that is no string are a GraphError there. An `@type` that is neither a string nor a list (a number,
null, a bool, an object) is taken as no type: the entity is of no type and no lookup finds it. The lookups of each
relation (`job_of`, `decode_of`, `job_of_raw`) and of the digests are built the
first time they are asked, so an entity edited after that is not seen again by the lookups already built. Build a
new Index after editing a graph.

The relations it follows are the entity model's (design item 1.1):
  - a Job (`qro:Job`, a CreateAction) lists its PUBs in `object`, and the files it made in `result`, among them its
    one raw result (a File that is also a `qro:RawResult`);
  - a Decode (`qro:Decode`, a CreateAction) lists the raw result it reads in `object`;
  - a Pub's index in its job's result is the last segment of its @id: `#pub-<job id>-<k>`, k one decimal digit.
A relation that is missing, or holds twice, is a GraphError (a ValueError): no step guesses which was meant.
"""
import re


class GraphError(ValueError):
    """The graph does not hold a relation a caller asked for, or holds it more than once."""


def types_of(entity):
    t = entity.get("@type")
    return [t] if isinstance(t, str) else list(t) if isinstance(t, list) else []


def ref_ids(value):
    """The @ids of a reference, or of a list of them; nothing for anything else."""
    return [v["@id"] for v in (value if isinstance(value, list) else [value])
            if isinstance(v, dict) and isinstance(v.get("@id"), str)]


_PUB_ID = re.compile(r".*-([0-9])", re.ASCII | re.DOTALL)


class Index:
    def __init__(self, md):
        graph = md.get("@graph") if isinstance(md, dict) else None
        if not isinstance(graph, list):
            raise GraphError("the metadata holds no list @graph")
        self.by_id = {}
        self._types = {}
        for e in graph:
            i = e.get("@id") if isinstance(e, dict) else None
            if not isinstance(i, str):
                raise GraphError("an entity without an @id")
            if i in self.by_id:
                raise GraphError(f"{i}: an @id twice in the graph")
            self.by_id[i] = e
            for t in types_of(e):
                if not isinstance(t, str):
                    raise GraphError(f"{i}: a type that is not a string")
                self._types.setdefault(t, []).append(e)
        self._holders = {}                         # (type, key) -> {ref id: [entities of that type naming it]}
        self._digests = None                       # sha256 -> [Files], built on first use

    # -- entities ------------------------------------------------------------------------------------------
    def of_type(self, t):
        """The entities of a type, in the graph's order."""
        return list(self._types.get(t, ()))

    def get(self, ref, type=None):
        """The entity a reference, or an @id, names; of `type` where one is given. GraphError otherwise."""
        i = ref["@id"] if isinstance(ref, dict) and "@id" in ref else ref
        e = self.by_id.get(i) if isinstance(i, str) else None
        if e is None:
            raise GraphError(f"{i}: names no entity in the graph")
        if type is not None and type not in types_of(e):
            raise GraphError(f"{i}: not a {type}")
        return e

    def refs(self, entity, key):
        """The @ids an entity's term refers to, in the order it lists them."""
        return ref_ids(entity.get(key))

    def one(self, entity, key, type=None):
        """The one entity a single-valued reference names: GraphError where the term is missing or names more."""
        ids = self.refs(entity, key)
        if len(ids) != 1:
            raise GraphError(f"{entity['@id']} {key}: names {len(ids)} entities, not one")
        return self.get(ids[0], type)

    def refs_of_type(self, entity, key, type):
        """The entities of a type among those an entity's term refers to. A reference to an IRI the graph does not
        hold, or to an entity of another type, is not one of them."""
        return [self.by_id[i] for i in self.refs(entity, key)
                if i in self.by_id and type in types_of(self.by_id[i])]

    # -- the model's relations -----------------------------------------------------------------------------
    def _holding(self, type, key):
        """{ref id: the entities of `type` whose `key` names it}, built once."""
        held = self._holders.get((type, key))
        if held is None:
            held = {}
            for e in self._types.get(type, ()):
                for i in dict.fromkeys(ref_ids(e.get(key))):
                    held.setdefault(i, []).append(e)
            self._holders[(type, key)] = held
        return held

    def _only(self, found, what, of):
        if len(found) != 1:
            raise GraphError(f"{of}: {len(found)} {what}, not one")
        return found[0]

    def job_of(self, pub):
        """The one Job whose `object` lists the Pub."""
        i = pub["@id"] if isinstance(pub, dict) else pub
        return self._only(self._holding("qro:Job", "object").get(i, []), "jobs list it", i)

    def pubs_of(self, job):
        """The Pubs a Job lists in `object`, in the order it lists them."""
        return self.refs_of_type(job, "object", "qro:Pub")

    def raw_of(self, job):
        """The one raw result among the files a Job made."""
        return self._only(self.refs_of_type(job, "result", "qro:RawResult"), "raw results among what it made",
                          job["@id"])

    def decode_of(self, raw):
        """The one Decode whose `object` lists the raw result."""
        i = raw["@id"] if isinstance(raw, dict) else raw
        return self._only(self._holding("qro:Decode", "object").get(i, []), "decodes read it", i)

    def job_of_raw(self, raw):
        """The one Job that made the raw result."""
        i = raw["@id"] if isinstance(raw, dict) else raw
        return self._only(self._holding("qro:Job", "result").get(i, []), "jobs made it", i)

    def files_by_sha256(self, digest):
        """The Files that state this digest, in the graph's order: found by digest, never by a name."""
        if self._digests is None:
            self._digests = {}
            for e in self._types.get("File", ()):
                if isinstance(e.get("sha256"), str):
                    self._digests.setdefault(e["sha256"], []).append(e)
        return list(self._digests.get(digest, ())) if isinstance(digest, str) else []

    def pub_index(self, pub):
        """The PUB's position in its job's result: the last segment of its @id, one decimal digit."""
        i = pub["@id"] if isinstance(pub, dict) else pub
        m = _PUB_ID.fullmatch(i)
        if not m:
            raise GraphError(f"{i}: a Pub's @id ends in -k, k one decimal digit: its PUB index")
        return int(m.group(1))
