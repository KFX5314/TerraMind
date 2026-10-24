"""Product-independent regressions for the metrics experiment."""
from certi.pipeline import dedupe
import asyncio

import pytest

from certi import llm
from certi.subgoal import align_new, complete_provision, existing_occurrence, fit_change_text, segments, words


def candidate(text, paragraph="4.2", probability=.8):
    return {"regulation": "SYNTHETIC", "paragraph": paragraph,
            "text": text, "probability": probability}


def test_distinct_limits_and_polarity_survive():
    cs = [candidate("The unit shall withstand 100 N."),
          candidate("The unit shall withstand 200 N."),
          candidate("The unit shall not withstand 100 N."),
          candidate("The unit shall withstand ≤ 100 N."),
          candidate("The unit shall withstand ≥ 100 N.")]
    assert len(dedupe(cs)) == 5


def test_same_words_in_different_source_occurrences_survive():
    assert len(dedupe([candidate("The unit shall be red.", "4.2"),
                       candidate("The unit shall be red.", "8.1")])) == 2


def test_exact_duplicates_keep_confidence_without_mutating_input():
    cs = [candidate("The unit shall be red.", probability=.6),
          candidate("The unit shall be red.", probability=.9)]
    assert dedupe(cs)[0]["probability"] == .9
    assert all("_n" not in c and "merged" not in c for c in cs)


def test_added_scope_is_not_an_existing_occurrence():
    assert existing_occurrence(12, 4, {4: {12}})
    assert not existing_occurrence(19, 4, {4: {12}})
    assert existing_occurrence(19, 4, {})


def test_long_provision_keeps_changed_tail():
    prefix = " ".join(["The equipment shall meet the condition."] * 22)
    def seg(pid, i, text):
        return {"pid": pid, "i": i, "text": text, "w": words(text)}
    old = [seg(1, 0, prefix), seg(1, 1, "The operating limit shall be 120 N.")]
    new = [seg(2, 0, prefix), seg(2, 1, "The operating limit shall be 240 N.")]
    a = {"pid": 1, "text": prefix, "w": words(prefix)}
    b = {"pid": 2, "text": prefix, "w": words(prefix)}
    aa, bb = complete_provision(a, b, old, new)
    assert "120 N" in aa["text"]
    assert "240 N" in bb["text"]


def test_short_requirement_does_not_absorb_sibling_obligations():
    a = {"pid": 1, "text": "The unit shall be red.", "w": words("The unit shall be red.")}
    b = {**a, "pid": 2}
    assert complete_provision(a, b, [], []) == (a, b)


def test_identical_step_aligns_with_its_original_procedure():
    step = "Hold the equipment stationary and select the operating direction."
    old_text = "Stationary procedure. " + step + " Apply the brake. Record the static load."
    new_texts = [old_text, "Moving procedure. " + step + " Release the brake. Record the moving load."]
    def para(i, text):
        return {"id": i, "kind": "para", "num": str(i), "label": str(i),
                "title": "", "text": text, "pages": [1]}
    old_doc = {"paragraphs": [para(0, old_text)]}
    new_doc = {"paragraphs": [para(i, t) for i, t in enumerate(new_texts)]}
    old_loc = {"pid": 0, "w": words(step)}
    assert align_new(old_loc, old_doc, new_doc, segments(new_doc))["pid"] == 0


def test_export_limit_is_validated_even_if_provider_ignores_schema(monkeypatch):
    async def oversized(**kwargs):
        return {"text": "x" * 2100}
    monkeypatch.setattr(llm, "call_json", oversized)
    with pytest.raises(llm.LLMError, match="2000 characters"):
        asyncio.run(fit_change_text("x" * 2200))


def test_complete_short_text_needs_no_rewrite(monkeypatch):
    async def unexpected(**kwargs):
        raise AssertionError("No model call needed")
    monkeypatch.setattr(llm, "call_json", unexpected)
    text = "The equipment shall withstand 140 N."
    assert asyncio.run(fit_change_text(text)) == text
