"""Evaluation only (reads expected.json AFTER a run's output is frozen).

* official offline scorer (regulation + page level)
* internal LLM-judge estimate of the requirement level: one-to-one matching of obligations per regulation.
  This is NOT the platform score - it is labelled as an internal estimate everywhere it is shown.
"""

from __future__ import annotations

import asyncio
import json
import subprocess
import sys

from . import llm, paths

JUDGE_SYSTEM = """You compare two lists of engineering requirements derived from the same UN Regulation for the same
product: an EXPECTED list (written by regulatory experts) and a SUBMITTED list. Match them one to one: a pair matches
only if both state the same engineering obligation - same subject/scope, same condition and same constraint (limits,
units, referenced tests). Wording may differ. A submitted requirement that bundles several expected obligations may
match at most one of them. Each id may appear in at most one pair. Return only real matches."""

JUDGE_SCHEMA = {
    "type": "object", "additionalProperties": False, "required": ["pairs"],
    "properties": {"pairs": {"type": "array", "items": {
        "type": "object", "additionalProperties": False, "required": ["submitted", "expected"],
        "properties": {"submitted": {"type": "string"}, "expected": {"type": "string"}}}}},
}


def f2(p: float, r: float) -> float:
    return 0.0 if (4 * p + r) == 0 else 5 * p * r / (4 * p + r)


async def judge(submission: dict, expected: dict) -> dict:
    regs = sorted({r["source"]["regulation"] for r in submission["requirements"]}
                  | {r["source"]["regulation"] for r in expected["requirements"]})
    pairs: list[tuple[str, str]] = []

    async def one(reg):
        sub = [r for r in submission["requirements"] if r["source"]["regulation"] == reg]
        exp = [r for r in expected["requirements"] if r["source"]["regulation"] == reg]
        if not sub or not exp:
            return []
        fmt = lambda rs: "\n".join(f"{r['id']} [{r['source'].get('paragraph', '')}] {r['text']}" for r in rs)
        res = await llm.call_json(system=JUDGE_SYSTEM, schema=JUDGE_SCHEMA, tag=f"judge:{reg}", effort="medium",
                                  content=f"Regulation {reg}\n\nEXPECTED:\n{fmt(exp)}\n\nSUBMITTED:\n{fmt(sub)}",
                                  max_tokens=32000)
        sub_ids, exp_ids = {r["id"] for r in sub}, {r["id"] for r in exp}
        used_s, used_e, out = set(), set(), []
        for p in res["pairs"]:
            if p["submitted"] in sub_ids and p["expected"] in exp_ids and p["submitted"] not in used_s \
                    and p["expected"] not in used_e:
                used_s.add(p["submitted"]); used_e.add(p["expected"]); out.append((p["submitted"], p["expected"]))
        return out

    for got in await asyncio.gather(*(one(r) for r in regs)):
        pairs += got
    n_sub, n_exp, tp = len(submission["requirements"]), len(expected["requirements"]), len(pairs)
    p = tp / n_sub if n_sub else 0.0
    r = tp / n_exp if n_exp else 0.0
    matched_s, matched_e = {a for a, _ in pairs}, {b for _, b in pairs}
    per_reg = {}
    for reg in regs:
        s_ids = [x["id"] for x in submission["requirements"] if x["source"]["regulation"] == reg]
        e_ids = [x["id"] for x in expected["requirements"] if x["source"]["regulation"] == reg]
        m = sum(1 for a, b in pairs if a in s_ids)
        per_reg[reg] = {"submitted": len(s_ids), "expected": len(e_ids), "matched": m,
                        "precision": m / len(s_ids) if s_ids else 0.0, "recall": m / len(e_ids) if e_ids else 0.0}
    return {
        "label": "internal LLM-judge estimate (not the platform score)",
        "precision": p, "recall": r, "f2": f2(p, r), "tp": tp, "n_submitted": n_sub, "n_expected": n_exp,
        "per_regulation": per_reg, "pairs": pairs,
        "missed": [x for x in expected["requirements"] if x["id"] not in matched_e],
        "extra": [x for x in submission["requirements"] if x["id"] not in matched_s],
    }


def local_score(sub_file, expected_file) -> dict:
    out = subprocess.run([sys.executable, str(paths.PKG / "tools" / "score_local.py"), str(sub_file),
                          "--expected", str(expected_file), "--json"], capture_output=True, text=True)
    return json.loads(out.stdout)


def report(run_id: str, judge_too: bool = False, judge: bool | None = None) -> dict:
    run_dir = paths.RUNS / run_id
    inputs = json.loads((run_dir / "inputs.json").read_text(encoding="utf-8"))
    exp_file = paths.expected_path(inputs["case_id"])
    sub_file = run_dir / "submission.json"
    res = {"local": local_score(sub_file, exp_file)}
    for k, v in res["local"].items():
        print(f"{k:<18} P={v['precision']:.3f} R={v['recall']:.3f} F2={f2(v['precision'], v['recall']):.3f}  "
              f"({v['n_submitted']} cited / {v['n_expected']} expected / {v['n_matched']} matched)")
    if judge or judge_too:
        sub = json.loads(sub_file.read_text(encoding="utf-8"))
        exp = json.loads(exp_file.read_text(encoding="utf-8"))
        j = llm.run(globals()["judge"](sub, exp))
        res["judge"] = j
        print(f"requirement (judge) P={j['precision']:.3f} R={j['recall']:.3f} F2={j['f2']:.3f}  "
              f"({j['n_submitted']} submitted / {j['n_expected']} expected / {j['tp']} matched)  [{j['label']}]")
        for reg, v in j["per_regulation"].items():
            print(f"   {reg:<10} sub={v['submitted']:>4} exp={v['expected']:>4} match={v['matched']:>4} "
                  f"P={v['precision']:.2f} R={v['recall']:.2f}")
    (run_dir / "eval.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    return res
