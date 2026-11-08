"""The rows P3's and P5's approved designs ask of the vocabulary (P0.10; P3's design, item 11, and P5's, item 12,
approved 2026-11-08), pinned whole: a row dropped, a word of a set changed, a term given a step, or a refusal moved
fails here by name. The sentences of the `statement` set are P3's design text (item 5's table); three of them are the
registry's texts, which this holds word for word. No CHECKED term is among them, as both designs say."""
import pytest

from controls import registry as R
from qro import vocabulary as V

STATEMENT = {
    "isolated-pipeline": "isolated from the pipeline",
    "drift-unmeasured": "not isolated from the pipeline: drift UNMEASURED, `none`",
    "strong-form-short": "not isolated from the pipeline: the strong form is not above epsilon",
    "question-varied": "not isolated from the pipeline: the question DIFFERS",
    "submitted-differs": "not isolated from the pipeline: what was submitted DIFFERS",
    "commit-unknown": "not isolated from the pipeline: the producing commit is `unknown`",
    "commit-differs": "not isolated from the pipeline: the producing commit DIFFERS",
    "compile-unheld": "not isolated from the pipeline: the compile DIFFERS and is not held",
    "device-alone": "the difference is the device's",
    "device-and-time": "the difference is the device's-and-its-time's",
    "one-device": "the runs ran on one device: the difference is its time's",
    "quantum-unpiped": "isolated as quantum: no, not isolated from the pipeline",
    "readout-unbounded": "isolated as quantum: no, readout's effect unbounded",
    "readout-short": "isolated as quantum: no, the strong form less the readout bound is not above epsilon",
    "integrity-dephased": "isolated as quantum against the dephased twin: no, the measure is integrity against it",
    "integrity-uniform": "isolated as quantum against the uniform twin: no, the measure is integrity against it",
    "quantum-dephased": "isolated as quantum against the dephased twin",
    "quantum-uniform": "isolated as quantum against the uniform twin",
}


def test_the_statement_set_is_the_eighteen_sentences_in_the_designs_order():
    assert V.WORDS["statement"] == STATEMENT and len(STATEMENT) == 18
    assert list(V.WORDS["statement"]) == list(STATEMENT), "the record lists a measure's statements in this order"


def test_a_statement_changed_by_a_word_fails_the_pin(monkeypatch):
    changed = dict(V.WORDS["statement"], **{"drift-unmeasured": "not isolated from the pipeline: drift UNMEASURED"})
    monkeypatch.setitem(V.WORDS, "statement", changed)
    assert V.WORDS["statement"] != STATEMENT


def test_the_registrys_three_sentences_are_the_statement_words_meanings_exactly():
    """Section 11's cells `single-runs`, `readout-unbounded` and `time-confounded` quote the sentences the record
    states; `not-interleaved` quotes the same one as `time-confounded`."""
    said = {"single-runs": "drift-unmeasured", "readout-unbounded": "readout-unbounded",
            "time-confounded": "device-and-time", "not-interleaved": "device-and-time"}
    for row, word in said.items():
        assert R.sentence(R.CONTROL[row]) == V.WORDS["statement"][word], row


def test_a_states_row_with_no_quoted_sentence_names_a_kept_refusal():
    c = R.CONTROL["unit-incomplete"]
    assert R.sentence(c) == "unit-incomplete" and V.REFUSAL["unit-incomplete"].effect == "kept"
    assert R.sentence(R.CONTROL["shot-moved"]) is None, "only a `states` row has a sentence"


def test_every_states_row_has_a_sentence():
    assert [c.name for c in R.CONTROLS if c.expected == "states" and R.sentence(c) is None] == []


WORD_SETS = {
    "comparison-kind": ["real", "rehearsal"],
    "means": ["differ", "agree", "unresolved"],
    "status": ["EQUAL", "DIFFERS", "CONTROLLED", "UNMEASURED"],
    "granularity": ["job", "crate"],
    "factor": ["question", "compile", "submitted", "commit", "device", "decode", "known-answer", "date"],
    "route": ["ibm-direct", "moth"],
}


@pytest.mark.parametrize("name", sorted(WORD_SETS))
def test_each_word_set_is_the_designs(name):
    assert list(V.WORDS[name]) == WORD_SETS[name] and all(V.WORDS[name].values())


def test_the_designs_meanings_of_a_few_words_are_pinned():
    w = V.WORDS
    assert w["comparison-kind"]["real"] == "a comparison that admits only qpu units"
    assert w["means"]["unresolved"] == "neither"
    assert w["status"]["UNMEASURED"] == "no bound exists; its absence word says why"
    assert w["granularity"]["crate"] == "it compares each crate's pooled jobs of one run with each of the other's"
    assert set(w["factor"].values()) == {"both runs share it, so no difference between them can show it"}
    assert w["route"]["moth"] == "the line sent to the owner"


def test_audit_stage_gains_comparison_and_the_stages_field_counts_four():
    assert list(V.WORDS["audit-stage"]) == ["crate-only", "compile", "qpy", "anchors", "comparison"]
    assert V.WORDS["audit-stage"]["comparison"] == "the comparison's record, re-derived from its runs' crates"
    assert next(f for f in V.AUDIT_RECORD if f.key == "stages").meaning.endswith("and any of the four")


NEW_TERMS = {
    "qro:comparisonKind": ("REPORTED", "word:comparison-kind", False, (), "P3", ("qro:Comparison",)),
    "qro:recipe": ("REPORTED", "digest", False, (), "P5", ("qro:Unit",)),
    "qro:contributor": ("REPORTED", "text", False, ("withheld",), "P5", ("qro:Unit",)),
    "qro:kitTag": ("REPORTED", "text", False, ("unknown",), "P5", ("qro:Unit",)),
    "qro:unitJobs": ("REPORTED", "ref", True, (), "P5", ("qro:Unit",)),
    "qro:route": ("REPORTED", "word:route", False, (), "P5", ("qro:Job",)),
}


@pytest.mark.parametrize("key", sorted(NEW_TERMS))
def test_each_new_term_is_the_designs_row(key):
    t = V.TERM[key]
    assert (t.kind, t.spelling, t.many, t.absent, t.owner, t.domain) == NEW_TERMS[key]
    assert (t.part, t.step) == ("body", None) and t.meaning


def test_no_term_of_p3_or_p5_is_checked_and_none_names_a_step():
    mine = [t for t in V.TERMS if t.owner in ("P3", "P5")]
    assert sorted(t.key for t in mine) == sorted(NEW_TERMS)
    assert [t.key for t in mine if t.kind == "CHECKED" or t.step is not None] == []


def test_the_new_types_are_the_designs_and_no_action():
    assert (V.TYPE["qro:Comparison"].owner, V.TYPE["qro:Comparison"].action) == ("P3", False)
    assert (V.TYPE["qro:Unit"].owner, V.TYPE["qro:Unit"].action) == ("P5", False)
    assert "qro:Comparison" not in V.ACTION_TYPES and "qro:Unit" not in V.ACTION_TYPES


KIT = ["once-only", "spend-usage", "spend-unit", "spend-cap", "plan-not-open", "kind-mismatch", "route-unsafe",
       "key-leak", "preflight-circuit", "preflight-chain", "preflight-options"]


def test_comparison_generated_is_p3s_refusal_at_comparison():
    r = V.REFUSAL["comparison-generated"]
    assert (r.where, r.effect, r.owner) == ("comparison", "refused", "P3")
    assert r.meaning.endswith("verdicts are computed only on the runs' data")


@pytest.mark.parametrize("name", KIT)
def test_each_kit_refusal_is_p5s_at_kit_and_refused(name):
    r = V.REFUSAL[name]
    assert (r.where, r.effect, r.owner) == ("kit", "refused", "P5") and r.meaning


def test_the_kit_refusals_are_the_designs_eleven_besides_p5s_three():
    assert sorted(r.name for r in V.REFUSALS if r.where == "kit") == sorted(KIT + ["kit-dirty", "unit-incomplete",
                                                                                    "not-interleaved"])


def test_a_refusal_that_may_be_a_verdict_is_a_verdict_word():
    for name in ["comparison-generated"] + KIT:
        assert name in V.WORDS["verdict"], name
    assert "selector-late" not in V.WORDS["verdict"], "a kept record is no refusal"


def test_joint_omission_takes_comparison_generated_with_the_studys_text():
    c = R.CONTROL["joint-omission"]
    assert (c.expected, c.refusal, c.owner) == ("refused", "comparison-generated", "P3")
    assert c.text == "refused: verdicts are computed only on the runs' data"
