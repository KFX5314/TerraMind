"""Offline requirement-level proxy calibrated to the platform (evaluation only).

One-to-one greedy matching of word-level similarity >= 0.65 within the same regulation reproduces the platform's
dev numbers (119 vs 120 matches, P 0.347 vs 0.350, R 0.626 vs 0.632 on dev-v2-frozen)."""

from __future__ import annotations

import json

from .subgoal import ratio, words

THRESHOLD = 0.65


def f2(p: float, r: float) -> float:
    return 0.0 if (4 * p + r) == 0 else 5 * p * r / (4 * p + r)


def match(submitted: list[dict], expected: list[dict], threshold: float = THRESHOLD) -> dict:
    """submitted/expected: lists with 'text' and source.regulation. Returns pairs and P/R/F2."""
    sw = [(s["source"]["regulation"], words(s["text"])) for s in submitted]
    gw = [(g["source"]["regulation"], words(g["text"])) for g in expected]
    pairs = sorted(((ratio(w, w2), i, k) for i, (r, w) in enumerate(gw) for k, (r2, w2) in enumerate(sw) if r == r2),
                   reverse=True)
    ug, uc, out = set(), set(), []
    for x, i, k in pairs:
        if x < threshold:
            break
        if i not in ug and k not in uc:
            ug.add(i)
            uc.add(k)
            out.append((k, i, round(x, 3)))
    tp = len(out)
    p = tp / len(submitted) if submitted else 0.0
    r = tp / len(expected) if expected else 0.0
    return {"label": f"lexical proxy (sim>={threshold}), calibrated to the platform", "precision": p, "recall": r,
            "f2": f2(p, r), "tp": tp, "n_submitted": len(submitted), "n_expected": len(expected), "pairs": out,
            "unmatched_submitted": [k for k in range(len(submitted)) if k not in uc],
            "unmatched_expected": [i for i in range(len(expected)) if i not in ug]}


def sweep(candidates: list[dict], expected: list[dict], thresholds=(0.0, 0.3, 0.4, 0.5, 0.6, 0.7)) -> list[dict]:
    """Export-threshold sweep on internal candidates (with 'probability', 'regulation', 'text')."""
    out = []
    for t in thresholds:
        sel = [{"text": c["text"], "source": {"regulation": c["regulation"]}} for c in candidates if c["probability"] >= t]
        m = match(sel, expected)
        out.append({"threshold": t, "n": len(sel), "tp": m["tp"], "precision": m["precision"], "recall": m["recall"],
                    "f2": m["f2"]})
    return out


def load_submission(path) -> list[dict]:
    d = json.loads(open(path, encoding="utf-8").read())
    return d["requirements"]
