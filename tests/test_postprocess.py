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


# ---------------------------------------------------------------------------------------------------- sub-goal style
def test_kept_wording_detects_paraphrase_but_not_amendment():
    old = "The road shall be flat, horizontal and dry, and the obstacle located between 1.0 m and 1.5 m."
    new_src = "The road shall be flat, horizontal and dry, and the obstacle located not more than 1.5 m."
    minimal = "The road shall be flat, horizontal and dry, and the obstacle located not more than 1.5 m."
    compressed = "The road (flat, horizontal, dry) and obstacle shall be at not more than 1.5 m."
    assert S.kept_wording(old, new_src, minimal)[0] == 1.0  # the amended words are not counted as lost
    kept, lost = S.kept_wording(old, new_src, compressed)
    assert kept < S.KEPT_MIN and lost


def test_kept_wording_ignores_context_absent_from_new_source():
    old = "For the cold-start test, the heater shall reach 20 °C within 60 s."
    new_src = "The heater shall reach 20 °C within 60 s."
    assert S.kept_wording(old, new_src, "The heater shall reach 20 °C within 60 s.")[0] == 1.0


def test_nearest_excludes_own_pair_and_prefers_close_labels():
    pool = [{"id": "R-1", "label": "6.6.1", "w": set(S.words("each test condition shall be tested"))},
            {"id": "R-2", "label": "6.6.2", "w": set(S.words("each test condition shall be tested"))},
            {"id": "R-3", "label": "2.1", "w": set(S.words("definitions of terms"))}]
    got = S.nearest(pool, "each test condition shall be tested twice", "6.6.1.4", 2, exclude="R-1")
    assert [p["id"] for p in got] == ["R-2", "R-3"]
    assert S.nearest(pool, "each test condition", "6.6.1.4", 1)[0]["id"] == "R-1"


def test_style_pairs_only_reliably_located():
    rows = [{"id": "R-1", "text": "req", "old": {"label": "5.1", "text": "src", "ratio": 0.9}},
            {"id": "R-2", "text": "req", "old": {"label": "5.2", "text": "src", "ratio": 0.2}},
            {"id": "R-3", "text": "req", "old": None}]
    assert [p["id"] for p in S.style_pairs(rows)] == ["R-1"]


def test_modal_mismatch():
    assert S.modal_mismatch("Tests without a target may be combined.", "Tests shall be allowed to be combined.") == {"shall"}
    assert S.modal_mismatch("Tests without a target may be combined.", "Tests without a target may be combined.") == set()
    assert S.modal_mismatch("The lamp shall not be red.", "The lamp shall not be red.") == set()
    assert S.modal_mismatch("(a) Position the vehicle.", "The procedure shall be to position the vehicle.") == set()  # no source modal


