Draft 4's re-check (Sonnet), 2026-10-14: its findings and notes, as transcribed by the lead.

PROVENANCE: the verifier's full report was delivered to the lead in-session. It was not yet written to any file
when this packet was frozen, so this is the lead's transcription of the findings and notes. Line numbers refer to
the frozen draft 4 (QRO-0.draft4.frozen.md). The report's bottom line was NOT READY: V1 to V8 were all answered
correctly and applied everywhere, and these five small text defects were found.

W1. Section 0 item 6, lines 150-151: "by at least 0.044" is a lower bound rounded up (the class of draft 2's R1).
    The verifier's Decimal reimplementation gives L(|diff|) = 0.04380713; the table and the isolation output say
    0.0438. The forbidden share's "0.004" is fine (0.004011). Fix: 0.043 or 0.0438.
W2. Question 9, line 1308: "docs/VALIDATION.md:1700" should be ":1701" ("leaving 247 of the 600" is at 1701 at
    3a73823). The numbers are right: the metrics charges sum to 353 s.
W3. Section 17 "Not changed", lines 1755-1756: "It is the most conservative of the three" is false at eps = 0.10.
    For M = 9 at eps = 0.10 the origin model (a) gives 8.7 s and 22.3 s against model (c)'s 10.3 s and 23.3 s;
    (a) is highest only at eps = 0.05. Fix: "the highest of the three at eps = 0.05", or drop the sentence.
W4. Section 13, lines 1199-1200: "draft 3 goes next" is stale. Fix: "Drafts 1 to 3 went past verifiers, and
    draft 4 goes next".
W5. README correction, lines 138-140 (low severity): "Each figure is from calibration_at_execution_v0.py" is false
    for three details the script did not print: the coupler (65, 66); the rise 0.0029 to 1; "not on its chain,
    qubits 0 to 15". All three are true, confirmed from the snapshots and gate lists. Fix: say they were read
    from the snapshot files and gate lists, or make the instrument print changed keys when there are ten or fewer.

Notes.
a. "The history returns a snapshot minutes after its stamp" (lines 493, 650) generalises from one snapshot of
   seven; the other six have only upper bounds of 25 to 84 min. Say "can return". "This study's inference"
   (line 500) should read BELIEVED.
b. Citation nits: base_primitive.py:155-175 (and section 15's 150-178) stop before the job-mode path at :198 and
   :206, which v0's jobs used. ibm_backend.py:316 is the configuration refresh, not a history query; only :367 is.
c. UNMEASURED without its absence word: line 623, the cells at lines 732-733, the single-runs control (line 1134)
   and line 1157.
d. Line 137 says the snapshots "hold the morning freezes' values", then marrakesh has 2 differing.
e. Section 6 says "Its link to a job is one of", but v0's records hold both the first-shot and the running query
   for every job. Say which is the job's link.
f. Line 1170: "the reads' MANIFESTs name moth-quantum's files": only the first does; the results MANIFEST names
   neither files nor commit.
g. Counts such as "6,211" cover qubit and gate values only. The 449 `general` and 97 `general_qlists` entries
   show 0 differences against the morning freezes on every snapshot, so no statement changes.
h. held() covers only listed files. Adding a check that the directory's file set equals the MANIFEST's would
   close an unlisted extra snapshot (which then exited 1 only through a format error on None).
i. The section 15 output hashes are of CRLF bytes, so they will differ on LF platforms.
j. Stale docstrings: v0_timing_and_drift.py says "draft 2" and lists four sections (the code has seven);
   sufficiency_v0.py implies both rules are given for the nine-job campaign, but only the planning rule is.
k. Lines 486-487: "v0's circuits do not use that coupler" holds for marrakesh's circuits; kingston's circuits do
   use kingston's (65, 66) coupler.
l. Line 1666's "for the next verifier" is now historical.

The two "not changed" items: the len(W) == 4368 reason holds; the max-aggregator reason is partly false (W3), the
decision harmless since every law charge is 9 s.
