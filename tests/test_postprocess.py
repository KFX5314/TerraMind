"""Deterministic checks of post-processing, evidence flags, sub-goal tokenizer, cache/budget (no data, no model calls)."""

import asyncio
import json

import pytest

from certi import llm, paths, pipeline
from certi import subgoal as S


def cand(text, paragraph="5.1", prob=0.8, regulation="UN R1", condition=""):
    return {"text": text, "paragraph": paragraph, "probability": prob, "regulation": regulation, "condition": condition}


# ---------------------------------------------------------------------------------------------------- dedupe
def test_dedupe_keeps_different_limits():
    out = pipeline.dedupe([cand("The force shall not exceed 100 N."), cand("The force shall not exceed 200 N.")])
    assert len(out) == 2
    assert out[0].get("similar") or out[1].get("similar")  # cross-listed for review, not merged


def test_dedupe_keeps_opposite_signs_and_operators():
    assert len(pipeline.dedupe([cand("The voltage shall be at least -10 V."), cand("The voltage shall be at least 10 V.")])) == 2
    assert len(pipeline.dedupe([cand("The force shall be <= 10 N."), cand("The force shall be >= 10 N.")])) == 2


def test_dedupe_keeps_polarity_condition_and_paragraph():
    assert len(pipeline.dedupe([cand("The lamp shall emit white light."), cand("The lamp shall not emit white light.")])) == 2
    assert len(pipeline.dedupe([cand("The lamp shall be red.", condition="for vehicles of category M1"),
                                cand("The lamp shall be red.", condition="for vehicles of category N1")])) == 2
    assert len(pipeline.dedupe([cand("The lamp shall be red.", paragraph="5.1"), cand("The lamp shall be red.", paragraph="6.2")])) == 2


def test_dedupe_still_merges_true_duplicates():
    out = pipeline.dedupe([cand("The lamp shall be red.", prob=0.6), cand("The lamp shall be red.", prob=0.9)])
    assert len(out) == 1 and out[0]["probability"] == 0.9 and out[0]["merged"] == ["The lamp shall be red."]


def test_dedupe_distinct_table_rows_survive():
    a = cand("For pulse 1, the ESA shall meet immunity test level -75 V (12V system) for 500 pulses.", "Annex 10 3.1")
    b = cand("For pulse 2a, the ESA shall meet immunity test level +37 V (12V system) for 500 pulses.", "Annex 10 3.1")
    assert len(pipeline.dedupe([a, b])) == 2


# ---------------------------------------------------------------------------------------------------- evidence flags
def test_fidelity_sees_dropped_negation():
    src, txt = "The lamp shall not emit white light.", "The lamp shall emit white light."
    assert pipeline.fidelity(src, txt) < 1.0
    assert pipeline.evidence_checks(src, txt)["polarity_ok"] is False
    assert pipeline.evidence_checks(src, src)["polarity_ok"] is True


def test_evidence_flags_changed_number():
    ok = pipeline.evidence_checks("The height shall be not less than 350 mm.", "The height shall be not less than 350 mm.")
    bad = pipeline.evidence_checks("The height shall be not less than 350 mm.", "The height shall be not less than 530 mm.")
    assert ok["numbers_ok"] is True and bad["numbers_ok"] is False


def test_norm_keeps_engineering_operators():
    assert pipeline._norm("≤ 10 N") != pipeline._norm("≥ 10 N")
    assert pipeline._norm("−10 V") == pipeline._norm("-10 V")


# ---------------------------------------------------------------------------------------------------- sub-goal tokenizer
def test_words_keep_sign_and_operator():
    assert S.words("The voltage shall be at least -10 V.") != S.words("The voltage shall be at least 10 V.")
    assert S.words("The force shall be ≤10 N.") != S.words("The force shall be ≥10 N.")
    assert S.words("at least −10 V") == S.words("at least -10 V")


def test_words_ranges_and_editorial_unchanged():
    assert S.words("between 10-20 mm") == ["between", "10-20", "mm"]
    assert S.words("6 seconds, 70%") == S.words("6 s, 70 per cent")


# ---------------------------------------------------------------------------------------------------- screening retry
def test_screen_retries_missing_decisions_and_flags_the_rest(monkeypatch):
    regs = ["A", "B", "C"]
    monkeypatch.setattr(paths, "index", lambda: [{"regulation": r} for r in regs])
    monkeypatch.setattr(paths, "regulation_entry", lambda r: {"title": r})
    monkeypatch.setattr(paths, "version_entry", lambda r, role: {"version_label": "1"})
    calls = []

    async def fake(profile, rs, tag):
        calls.append((tuple(rs), tag))
        dec = lambda r: {"regulation": r, "decision": "applicable", "basis": "device_approval", "reason": "x", "probability": 0.9}
        return {r: dec(r) for r in rs if not (tag == "screen" and r != "A") and not (tag == "screen:retry" and r == "C")}

    monkeypatch.setattr(pipeline, "_screen_call", fake)
    out = {d["regulation"]: d for d in asyncio.run(pipeline.screen({}))}
    assert calls == [(("A", "B", "C"), "screen"), (("B", "C"), "screen:retry")]
    assert out["B"]["probability"] == 0.9 and not out["B"].get("needs_review")
    assert out["C"]["needs_review"] is True
    assert pipeline.selected_regulations(list(out.values())) == ["A", "B"]  # undecided ones are not auto-selected


# ---------------------------------------------------------------------------------------------------- cache and budget
def test_cache_ignored_for_smaller_max_tokens(monkeypatch, tmp_path):
    monkeypatch.setattr(paths, "CACHE", tmp_path)
    monkeypatch.setattr(llm, "_key", lambda payload: "ab" + "0" * 62)
    (tmp_path / "ab").mkdir()
    (tmp_path / "ab" / ("ab" + "0" * 62 + ".json")).write_text(
        json.dumps({"tag": "t", "max_tokens": 64000, "result": {"cached": True}}), encoding="utf-8")

    async def boom(kwargs):
        raise RuntimeError("model called")

    monkeypatch.setattr(llm, "_stream", boom)
    kw = dict(system="s", content="c", schema={}, tag="t")
    assert asyncio.run(llm.call_json(**kw, max_tokens=64000)) == {"cached": True}
    assert asyncio.run(llm.call_json(**kw, max_tokens=70000)) == {"cached": True}
    with pytest.raises(RuntimeError, match="model called"):
        asyncio.run(llm.call_json(**kw, max_tokens=1000))


def test_cache_entry_without_max_tokens_still_hits(monkeypatch, tmp_path):
    monkeypatch.setattr(paths, "CACHE", tmp_path)
    monkeypatch.setattr(llm, "_key", lambda payload: "cd" + "0" * 62)
    (tmp_path / "cd").mkdir()
    (tmp_path / "cd" / ("cd" + "0" * 62 + ".json")).write_text(json.dumps({"tag": "t", "result": {"old": 1}}), encoding="utf-8")
    assert asyncio.run(llm.call_json(system="s", content="c", schema={}, tag="t", max_tokens=1000)) == {"old": 1}


def test_budget_is_per_run():
    async def spend():
        llm.budget().add(3.0)
        return llm.spent()

    assert llm.run(spend()) == 3.0
    assert llm.run(spend()) == 3.0  # the second run does not inherit the first run's spend


def test_role_config_defaults_to_global_model(monkeypatch):
    monkeypatch.delenv("CLAUDE_EXTRACT_MODEL", raising=False)
    monkeypatch.delenv("CLAUDE_EXTRACT_EFFORT", raising=False)
    assert llm.role_model("extract") == llm.MODEL and llm.role_effort("extract") == "high"
    monkeypatch.setenv("CLAUDE_EXTRACT_MODEL", "claude-sonnet-5-5")
    monkeypatch.setenv("CLAUDE_EXTRACT_EFFORT", "medium")
    assert llm.role_model("extract") == "claude-sonnet-5-5" and llm.role_effort("extract") == "medium"
    assert llm.role_model("audit") == llm.MODEL  # other roles unaffected
