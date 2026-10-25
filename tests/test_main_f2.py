"""Main-goal export rules (no API calls)."""

import json

from certi import paths, pipeline


def test_annex_and_appendix_items_need_the_annex_threshold():
    thr = pipeline.ANNEX_THRESHOLD
    assert thr >= pipeline.DEFAULT_THRESHOLD
    assert pipeline.export_threshold({"paragraph": "Annex 6 Part 4 3"}, 0.5) == thr
    assert pipeline.export_threshold({"paragraph": "Appendix 7 2.1"}, 0.5) == thr
    assert pipeline.export_threshold({"paragraph": "6.10.4.2"}, 0.5) == 0.5
    # a stricter global threshold is never loosened by the annex rule
    assert pipeline.export_threshold({"paragraph": "Annex 9 3.1"}, 0.9) == 0.9


def test_annex_rule_keeps_every_main_body_export_of_the_best_run():
    reqs = json.loads((paths.RUNS / "dev-v6-dedupe" / "requirements.json").read_text(encoding="utf-8"))
    for c in reqs:
        if not c["paragraph"].startswith(("Annex", "Appendix")):
            assert (c["probability"] >= pipeline.export_threshold(c, 0.5)) == c["exported"]


def test_locate_skips_paragraphs_without_any_overlapping_window():
    from certi import subgoal as S
    segs = [{"pid": 0, "label": "1", "pages": [1], "i": 0, "text": "", "w": []},
            {"pid": 1, "label": "2", "pages": [2], "i": 0, "text": "The lamp shall be red.",
             "w": S.words("The lamp shall be red.")}]
    hit = S.locate(S.words("The lamp shall be red."), segs, pids=[0, 1])
    assert hit["label"] == "2"
    assert S.locate(S.words("unrelated words"), segs[:1], pids=[0]) is None
