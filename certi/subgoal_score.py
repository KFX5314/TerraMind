"""Evaluation only: sub-goal changes vs expected.json (internal estimate, not the platform score)."""

from __future__ import annotations

import json
from pathlib import Path

from .subgoal import ratio, words


def score(sub: dict, exp: dict) -> dict:
    s_flag = {c["requirement_id"]: c["change"] for c in sub["changes"] if c["requirement_id"]}
    e_flag = {c["requirement_id"]: c["change"] for c in exp["changes"] if c["requirement_id"]}
    flagged_hit = [i for i in e_flag if i in s_flag]
    type_ok = [i for i in flagged_hit if s_flag[i] == e_flag[i]]
    s_add = [c for c in sub["changes"] if c["change"] == "added"]
    e_add = [c for c in exp["changes"] if c["change"] == "added"]
    used, add_hits = set(), 0
    for e in e_add:
        best, bi = 0.0, None
        for k, s in enumerate(s_add):
            if k in used:
                continue
            r = ratio(words(e["new_text"]), words(s["new_text"]))
            same_para = (e.get("source") or {}).get("paragraph") == (s.get("source") or {}).get("paragraph")
            r += 0.1 if same_para else 0
            if r > best:
                best, bi = r, k
        if bi is not None and best >= 0.55:
            used.add(bi)
            add_hits += 1
    n_exp = len(e_flag) + len(e_add)
    n_sub = len(s_flag) + len(s_add)
    tp = len(type_ok) + add_hits
    return {
        "label": "internal estimate (not the platform score)",
        "recall": tp / n_exp if n_exp else 0, "precision": tp / n_sub if n_sub else 0,
        "flagged_recall": len(flagged_hit) / len(e_flag) if e_flag else 0,
        "type_accuracy": len(type_ok) / len(flagged_hit) if flagged_hit else 0,
        "added_recall": add_hits / len(e_add) if e_add else 0,
        "n_submitted": n_sub, "n_expected": n_exp,
        "missed_flags": sorted(set(e_flag) - set(s_flag)), "extra_flags": sorted(set(s_flag) - set(e_flag)),
    }


def report(sub_file: Path, exp_file: Path) -> dict:
    res = score(json.loads(Path(sub_file).read_text(encoding="utf-8")),
                json.loads(Path(exp_file).read_text(encoding="utf-8")))
    print(json.dumps(res, indent=1))
    return res
