# qro/data

- **ro-crate-1.3-context.jsonld**: RO-Crate 1.3's JSON-LD context, as served at
  https://w3id.org/ro/crate/1.3/context, which redirected to
  https://www.researchobject.org/ro-crate/specification/1.3/context.jsonld.
  - Fetched on 2026-10-14: 196,942 bytes, SHA-256
    `5a3df1a43185501db4d45cdde5a478c57eeb1d673eedfe400488fc4c4b21dd91`.
    qro/vocabulary.py pins that digest, and the strict reader refuses to load
    any other bytes.
  - Its own `license` is CC0 1.0
    (https://creativecommons.org/publicdomain/zero/1.0/). It is kept as
    fetched, byte for byte.
  - The strict reader uses its keys, and only its keys:
    - a key the context defines, but QRO-Crate's vocabulary gives no kind,
      is refused as `field-kind`;
    - a key in neither is refused as `term-unknown`.
