"""Deterministic checks of dedupe, fidelity and the sub-goal tokenizer (no data, no model calls)."""

from certi import pipeline
from certi import subgoal as S


def cand(text, paragraph="5.1", prob=0.8, regulation="UN R1", condition=""):
    return {"text": text, "paragraph": paragraph, "probability": prob, "regulation": regulation,
            "condition": condition, "version": "1"}


# ---------------------------------------------------------------------------------------------------- dedupe
def test_dedupe_keeps_different_limits():
    assert len(pipeline.dedupe([cand("The force shall not exceed 100 N."), cand("The force shall not exceed 200 N.")])) == 2


def test_dedupe_keeps_opposite_signs_and_operators():
    assert len(pipeline.dedupe([cand("The voltage shall be at least -10 V."), cand("The voltage shall be at least 10 V.")])) == 2
    assert len(pipeline.dedupe([cand("The force shall be <= 10 N."), cand("The force shall be >= 10 N.")])) == 2


def test_dedupe_keeps_polarity_condition_and_paragraph():
    assert len(pipeline.dedupe([cand("The lamp shall emit white light."), cand("The lamp shall not emit white light.")])) == 2
    assert len(pipeline.dedupe([cand("The lamp shall be red.", condition="for vehicles of category M1"),
                                cand("The lamp shall be red.", condition="for vehicles of category N1")])) == 2
    assert len(pipeline.dedupe([cand("The lamp shall be red.", paragraph="5.1"), cand("The lamp shall be red.", paragraph="6.2")])) == 2


def test_dedupe_still_merges_exact_duplicates_keeping_highest_probability():
    out = pipeline.dedupe([cand("The lamp shall be red.", prob=0.6), cand("The lamp shall be red.", prob=0.9)])
    assert len(out) == 1 and out[0]["probability"] == 0.9


def test_dedupe_distinct_table_rows_survive():
    a = cand("For pulse 1, the ESA shall meet immunity test level -75 V (12V system) for 500 pulses.", "Annex 10 3.1")
    b = cand("For pulse 2a, the ESA shall meet immunity test level +37 V (12V system) for 500 pulses.", "Annex 10 3.1")
    assert len(pipeline.dedupe([a, b])) == 2


# ---------------------------------------------------------------------------------------------------- fidelity
def test_fidelity_sees_flipped_polarity():
    assert pipeline.fidelity("The lamp shall not emit white light.", "The lamp shall emit white light.") < 0.5
    assert pipeline.fidelity("The lamp shall not emit white light.", "The lamp shall not emit white light.") == 1.0


# ---------------------------------------------------------------------------------------------------- sub-goal tokenizer
def test_words_keep_sign_and_operator():
    assert S.words("The voltage shall be at least -10 V.") != S.words("The voltage shall be at least 10 V.")
    assert S.words("The force shall be ≤10 N.") != S.words("The force shall be ≥10 N.")
    assert S.words("at least −10 V") == S.words("at least -10 V")


def test_words_ranges_and_editorial_unchanged():
    assert S.words("between 10-20 mm") == ["between", "10-20", "mm"]
    assert S.words("6 seconds, 70%") == S.words("6 s, 70 per cent")
