"""Deterministic checks (no model calls).  .venv/Scripts/python -m pytest -q tests"""

import json
import subprocess
import sys

from certi import ingest, paths, pipeline
from certi import subgoal as S
from certi.eval_parser import para_key


def test_inputs_never_include_expected():
    inp = pipeline.load_case_inputs("dev-rear-lamp")
    blob = json.dumps(inp)
    assert "expected" not in blob.lower()
    assert inp["spec"] and inp["images"]


def test_parser_finds_gold_labels_on_gold_pages():
    gold = json.loads(paths.expected_path("dev-rear-lamp").read_text(encoding="utf-8"))["requirements"]
    hits = 0
    for r in gold:
        doc = ingest.load(r["source"]["regulation"], "base")
        key = para_key(r["source"].get("paragraph"))
        if any(para_key(p["label"]) == key and r["source"]["page"] in p["pages"] for p in doc["paragraphs"]):
            hits += 1
    assert hits / len(gold) >= 0.97


def test_annex_and_part_labels():
    labels = {p["label"] for p in ingest.load("UN R150", "base")["paragraphs"]}
    assert "Annex 4 Part 1 1.2" in labels
    assert "5.7" in {p["label"] for p in ingest.load("UN R48", "base")["paragraphs"]}  # "5.7 Grouped" (no dot)


def test_page_resolution_multi_page_paragraph():
    # R48 6.7.4.2.1 sits on page 46 of the base PDF
    assert pipeline.resolve_page("UN R48", "6.7.4.2.1", "Above the ground, not less than 350 mm") == 46


def test_subgoal_alignment_matches_dev_flags():
    folder = paths.subgoal_dir("subgoal-dev")
    old_reqs = json.loads((folder / "requirements_old.json").read_text(encoding="utf-8"))
    exp = json.loads((folder / "expected.json").read_text(encoding="utf-8"))
    od = ingest.load_file(folder / "old.pdf", "UN R175", "old", "0.1.0")
    nd = ingest.load_file(folder / "new.pdf", "UN R175", "new", "1.0.0")
    os_, ns = S.segments(od), S.segments(nd)
    lp: dict = {}
    for p in od["paragraphs"]:
        lp.setdefault(p["label"], []).append(p["id"])
    flags = {}
    for r in old_reqs:
        ol = S.locate(S.words(r["text"]), os_, lp.get(r["source"].get("paragraph")))
        if ol is None or ol["ratio"] < 0.35:
            ol = S.locate(S.words(r["text"]), os_)
        nl = S.locate(ol["w"], ns)
        if nl is None or nl["ratio"] < S.MODIFIED_MIN:
            flags[r["id"]] = "removed"
        elif not S.substantive_same(ol, nl, od, nd):
            flags[r["id"]] = "modified"
    gold = {c["requirement_id"]: c["change"] for c in exp["changes"] if c["requirement_id"]}
    assert flags == gold


def test_editorial_notation_is_not_a_change():
    assert S.words("6 seconds, 70%") == S.words("6 s, 70 per cent")


def test_exports_validate():
    for f in sorted(paths.RUNS.glob("*/submission.json"))[:3]:
        r = subprocess.run([sys.executable, str(paths.PKG / "tools" / "validate.py"), str(f)], capture_output=True, text=True)
        assert r.returncode == 0, r.stdout + r.stderr


def test_signs_and_inequalities_are_meaningful():
    assert S.words("at least -10 V") != S.words("at least 10 V")
    assert S.words("shall be ≤10 N") != S.words("shall be ≥10 N")


def test_fidelity_detects_flipped_polarity():
    assert pipeline.fidelity("The lamp shall not emit white light.", "The lamp shall emit white light.") < 0.5
    assert pipeline.fidelity("The lamp shall not emit white light.", "The lamp shall not emit white light.") == 1.0
