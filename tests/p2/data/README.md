# P2.1's data: copies of Quantum-Film's files

Ten files of Quantum-Film's repository, moth-quantum, copied byte for byte and never re-encoded (LF, as they are
there), from commit `3a738230286385664cd83c9c0a04fe33a5e2348a` (3a73823): kingston's morning bundle of 2026-10-05, its four gate lists, its four
logical circuits and its manifest, and the source circuit whose law is the pauli-4x4 shelf's. 10 files,
157,309 bytes. Only P2's tests read them: the real-size exact hold, the law circuit, and the real crate that
tests/p2/p2_builder.py writes. The privacy gate reads them too; they hold no key, no account and no IBM job id (the
bundle is the compile's, frozen before any job ran).

| file | bytes | SHA-256 | its path in moth-quantum at 3a73823 |
|---|---|---|---|
| circuit-ed767c01bd4b851d.qasm | 5,394 | `ed767c01bd4b851d08993da80f715676e345fc95a10f3bda05400f738e400b36` | moth-quantum `docs/records/2026-09-25/p3/circuit-ed767c01bd4b851d.qasm` |
| coherence-xx.gates.json | 39,990 | `bade907e4dcfc4e24a2633aa489e57dcdbfdf4f87a018379e01bd3832a4dab0e` | moth-quantum `docs/records/2026-10-05/ibm/ibm_kingston/bundle/coherence-xx.gates.json` |
| coherence-xx.qasm | 5,932 | `bc4c3f12aa1f366abd28746ae7d22c8f6a7cfdb5ab6e926fe94b058e4072220f` | moth-quantum `docs/records/2026-10-05/ibm/ibm_kingston/bundle/coherence-xx.qasm` |
| coherence-yy.gates.json | 39,987 | `f9095bbc308d04085eb67e0059a13fdd13af64d6162fbe9fd48d2c9472a3e3c1` | moth-quantum `docs/records/2026-10-05/ibm/ibm_kingston/bundle/coherence-yy.gates.json` |
| coherence-yy.qasm | 5,952 | `0c57183b5e86c3091ceab22deb3f4cc3387a8379febe7ba22e1841e03d98b5f0` | moth-quantum `docs/records/2026-10-05/ibm/ibm_kingston/bundle/coherence-yy.qasm` |
| known-answer.gates.json | 3,008 | `ac3c9653d8975bfb4e8acc7318561f102ff570b901d8082b127e6f71ebea0515` | moth-quantum `docs/records/2026-10-05/ibm/ibm_kingston/bundle/known-answer.gates.json` |
| known-answer.qasm | 611 | `60c78957bf47b2b2bb8053b2e2103fa2bf1373752b85acfdc4bd37037f22ff49` | moth-quantum `docs/records/2026-10-05/ibm/ibm_kingston/bundle/known-answer.qasm` |
| law.gates.json | 39,992 | `5467463244f7b047492fdb63b63995174c9c0dfab6145697be2b4cbbed9fb248` | moth-quantum `docs/records/2026-10-05/ibm/ibm_kingston/bundle/law.gates.json` |
| law.qasm | 5,916 | `33cfeaa15e5ab0af031531d6b0bdbaee4df311196ca422fe6b927ee783e35fc7` | moth-quantum `docs/records/2026-10-05/ibm/ibm_kingston/bundle/law.qasm` |
| manifest.json | 10,527 | `6894a01142e24b2f47c13f19a80ef6c9ed48e26bd94285ba3035cce31881b656` | moth-quantum `docs/records/2026-10-05/ibm/ibm_kingston/bundle/manifest.json` |

The source circuit is one blob at two paths of moth-quantum, its 2026-09-25 and 2026-09-26 records; the table names
the first.

Their licence is Quantum-Film's: the MIT License, whose copyright and permission notice moth-quantum's `LICENSE` at
3a73823 states as follows, and which these copies carry with them.

```text
MIT License

Copyright (c) 2026 Logan W.

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```
