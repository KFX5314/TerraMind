"""Held-out front bumper, round 3: three offline candidates derived from the scored-best 450 file.
Zero model calls: saved extraction candidates, local PDFs (PyMuPDF), deterministic checks only.
usage: python analysis/build_heldout_round3.py"""
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

import pymupdf

ROOT = Path("C:/Users/saish/Certivity")
BEST = ROOT / "main-f2-eval/artifacts/evaluations/heldout-f2-offline-alternatives-20261025/eval-balanced-source-faithful.json"
BEST_SHA = "9c4cbac94ffe34f6ac031744f277d1aade0ce46153f648b2a4d4175725b6b936"
POOL = ROOT / "TeraMind/TerraMind/artifacts/runs/heldout-v1/requirements.json"
PKG = ROOT / "industrial-ai-hackathon"
OUT = ROOT / "main-f2-eval/artifacts/evaluations/heldout-f2-round3-20261025"
PY = ROOT / "TeraMind/TerraMind/.venv/Scripts/python.exe"

# ---------------------------------------------------------------- removal groups (each with an independent reason)
R94_REASON = ("UN R94 is whole-vehicle occupant protection in a frontal collision: every exported item is a dummy injury "
              "criterion (HPC, NIC, ThCC, V*C, FFC, TCFC, TI, knee slide) or a full-vehicle crash condition. A bumper is "
              "not approved under R94 and cannot be engineered or tested against these limits as a component. Official "
              "regulation precision 87.5% with recall 100% says one of the eight cited regulations is not in the "
              "reference set; R94 is the only one whose scope is not a product-level obligation of the bumper.")
ADMIN = {  # conformity of production / approval paperwork: duties of the manufacturer's production control or authority
    "R-0001": "UN R10 3.2.6: marking of the samples submitted with the application for approval (paperwork step).",
    "R-0004": "UN R10 4.1.3: approval route for intentional RF transmitters (administrative approval condition).",
    "R-0154": "UN R10 9.1: conformity of production (production control duty).",
    "R-0156": "UN R10 9.3.1: conformity-of-production verification of series samples.",
    "R-0157": "UN R10 9.3.2: conformity-of-production verification of series samples.",
    "R-0158": "UN R10 9.3.3: conformity-of-production verification of series samples.",
    **{i: "UN R48 Annex 9: 'For the control of conformity of production' check of installed lamps (production control)."
       for i in ("R-0779", "R-0780", "R-0781", "R-0782", "R-0783", "R-0786", "R-0787", "R-0788", "R-0789")},
    **{i: "UN R148 Annex 4: minimum requirements for conformity-of-production control (sampling)."
       for i in ("R-1120", "R-1121", "R-1123")},
    **{i: "UN R148 Annex 5: minimum requirements for sampling by an inspector (conformity of production)."
       for i in ("R-1128", "R-1129", "R-1131")},
}
RESTATE = {i: ("UN R10 Appendix 6/7: reference-limit graph restating the 30-1000 MHz ESA broadband/narrowband limits "
               "already exported from the main text (paragraphs 6.5/6.6).")
           for i in ("R-0159", "R-0160", "R-0161", "R-0162", "R-0163", "R-0164")}
LAB_EQUIPMENT = {  # laboratory set-up of the emission measurement, not a requirement on the ESA
    "R-0222": "UN R10 Annex 7 3.4: ambient-noise check of the test site.",
    "R-0223": "UN R10 Annex 7 3.4: ambient-noise margin of the test site.",
    "R-0225": "UN R10 Annex 7 4.2: peak-detector correction factor (measurement equipment).",
    "R-0226": "UN R10 Annex 7 4.3: spectrum analyser / scanning receiver (measurement equipment).",
    "R-0233": "UN R10 Annex 7 4.4: harness position relative to the antenna (test set-up).",
    "R-0245": "UN R10 Annex 8 4.2: average detector (measurement equipment).",
}
LAB_METHOD = {  # remaining Annex 7/8 method statements: removed only in the precision candidate
    i: "UN R10 Annex 7/8 measurement-method statement (laboratory procedure); dev expert cited none of Annex 7/8."
    for i in ("R-0216", "R-0217", "R-0219", "R-0224", "R-0238", "R-0239", "R-0240", "R-0244")}
DRL_HEAT = {i: ("UN R148 Annex 6: heat-resistance laboratory test of a daytime running lamp; a DRL is not identified "
                "in the specification or drawing.") for i in ("R-1135", "R-1136", "R-1137", "R-1144", "R-1145")}
ANNEX2 = {i: ("UN R148 Annex 2: device-level geometric-visibility table entry; installation visibility is already "
              "covered by UN R48 section 6, and front DI / position / DRL / side-marker functions are not established.")
          for i in ("R-1101", "R-1106", "R-1107", "R-1110", "R-1111")}  # keeps R-1105 (side direction indicator)

# ---------------------------------------------------------------- recoveries from saved, withheld candidates
ADD_B = {
    "R-0385": "UN R42 6.1.4: post-impact criterion; siblings 6.1.1, 6.1.2, 6.1.3 and 6.1.5 are already exported.",
    "R-0895": "UN R127 Annex 5 1.11: lower-legform-to-bumper test condition; siblings 1.4/1.5/1.10/1.12 exported.",
    "R-0901": "UN R127 Annex 5 1.6: impact direction of the lower-legform-to-bumper test; siblings exported.",
    "R-0902": "UN R127 Annex 5 1.7: impactor height in the lower-legform-to-bumper test; siblings exported.",
    "R-0903": "UN R127 Annex 5 1.8: free flight at impact in the lower-legform-to-bumper test; siblings exported.",
    "R-0412": "UN R42 Annex 3 2.7.3: impactor placement for the longitudinal impact test; 2.7.1/2.7.2/2.7.5 exported.",
    "R-0413": "UN R42 Annex 3 2.7.4: vehicle alignment for the longitudinal impact test; 2.7.1/2.7.2/2.7.5 exported.",
    "R-0416": "UN R42 Annex 3 2.8.2: impactor placement for the corner impact test; 2.8.1/2.8.3/2.8.4 exported.",
    "R-0419": "UN R42 Annex 3 2.8.3: vehicle alignment for the corner impact test; 2.8.1/2.8.3/2.8.4 exported.",
}
ADD_C = {
    **{i: "UN R42 Annex 3 2.1/2.2: vehicle condition for the low-speed impact test of the protective device."
       for i in ("R-0390", "R-0391", "R-0392", "R-0393", "R-0394", "R-0395")},
    "R-0904": "UN R127 Annex 5 2.4: upper-legform-to-bumper measuring points; 2.5/2.7 already exported.",
    "R-0908": "UN R127 Annex 5 2.6: upper-legform impact direction; 2.5/2.7 already exported.",
    "R-0909": "UN R127 Annex 5 2.6: upper-legform vertical position at first contact; 2.5/2.7 already exported.",
    "R-0910": "UN R127 Annex 5 2.6: upper-legform lateral position at first contact; 2.5/2.7 already exported.",
    "R-0866": "UN R127 5.1.1: the flexible lower legform impactor used for the bumper test shall be certified.",
    "R-0869": "UN R127 5.1.2: the upper legform impactor used for the bumper test shall be certified.",
}

CANDIDATES = {
    "A-precision": {"remove": {"R94": None, **ADMIN, **RESTATE, **LAB_EQUIPMENT, **LAB_METHOD, **DRL_HEAT, **ANNEX2},
                    "add": {"R-0385": ADD_B["R-0385"]}},
    "B-balanced": {"remove": {"R94": None, **ADMIN, **RESTATE, **LAB_EQUIPMENT, **DRL_HEAT}, "add": ADD_B},
    "C-recall": {"remove": dict(ADMIN), "add": {**ADD_B, **ADD_C}},
}


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def norm(s):
    return re.sub(r"\s+", " ", re.sub(r"[^0-9a-z%°.,±<>=+\- ]", " ", s.casefold())).strip()


def quote_on_page(c):
    pdf = PKG / "regulations/pdf" / c["regulation"].replace(" ", "_") / "base" / f"{c['regulation'].replace(' ', '_')}_base.pdf"
    doc = pymupdf.open(pdf)
    if not (1 <= c["page"] <= doc.page_count):
        return False, doc.page_count
    q = norm(c.get("quote") or c["text"])[:50]
    pages = [doc[c["page"] - 1].get_text()] + ([doc[c["page"]].get_text()] if c["page"] < doc.page_count else [])
    return any(q[:40] in norm(t) for t in pages), doc.page_count


# the R42 Annex 3 source says "should" for these placement/alignment steps; keep the source modal (as for 2.7.5/2.8.4)
MODAL_FIX = {"R-0412": ("shall be placed", "should be placed"), "R-0413": ("shall be aligned", "should be aligned"),
             "R-0416": ("shall be placed", "should be placed"), "R-0419": ("shall be aligned", "should be aligned")}


def to_req(c):
    text = c["text"]
    if c["id"] in MODAL_FIX:
        old, new = MODAL_FIX[c["id"]]
        assert text.count(old) == 1, c["id"]
        text = text.replace(old, new)
    return {"id": c["id"], "text": text[:2000],
            "source": {"regulation": c["regulation"], "version": c["version"], "page": c["page"],
                       "paragraph": c["paragraph"]},
            **({"test_case": c["test_case"]} if c.get("test_case") else {})}


def main():
    assert sha(BEST) == BEST_SHA, "current best file changed: stop"
    best = json.loads(BEST.read_text(encoding="utf-8"))
    pool = {c["id"]: c for c in json.loads(POOL.read_text(encoding="utf-8"))}
    OUT.mkdir(parents=True, exist_ok=True)
    report = {"parent": str(BEST), "parent_sha256": BEST_SHA, "candidates": {}}
    for name, spec in CANDIDATES.items():
        reqs = list(best["requirements"])
        removed, added = [], []
        drop_r94 = "R94" in spec["remove"]
        keep = []
        for r in reqs:
            if drop_r94 and r["source"]["regulation"] == "UN R94":
                removed.append({"id": r["id"], "text": r["text"], "source": r["source"], "reason": R94_REASON})
            elif r["id"] in spec["remove"]:
                removed.append({"id": r["id"], "text": r["text"], "source": r["source"], "reason": spec["remove"][r["id"]]})
            else:
                keep.append(r)
        missing = [i for i in spec["remove"] if i != "R94" and i not in {r["id"] for r in reqs}]
        assert not missing, (name, "removal ids not in the 450 file", missing)
        have = {r["id"] for r in keep}
        for i, why in spec["add"].items():
            c = pool[i]
            assert i not in have and not c["exported"], (name, i, "already exported")
            ok, n = quote_on_page(c)
            assert ok, (name, i, "saved quote not found on cited PDF page", c["page"])
            keep.append(to_req(c))
            added.append({"id": i, "text": to_req(c)["text"], "source": to_req(c)["source"], "quote": c.get("quote"),
                          "saved_probability": c["probability"], "applicability": c.get("applicability"),
                          "quote_on_cited_page": ok, "reason": why})
        ids = [r["id"] for r in keep]
        assert len(ids) == len(set(ids)), (name, "duplicate ids")
        sub = {"team_id": best["team_id"], "case_id": best["case_id"], "requirements": keep}
        path = OUT / f"cand-{name}.json"
        path.write_text(json.dumps(sub, ensure_ascii=False, indent=1), encoding="utf-8")
        v = subprocess.run([str(PY), str(PKG / "tools/validate.py"), str(path), "--index",
                            str(PKG / "regulations/index.json"), "--strict"], capture_output=True, text=True)
        per_reg = {}
        for r in keep:
            per_reg[r["source"]["regulation"]] = per_reg.get(r["source"]["regulation"], 0) + 1
        report["candidates"][name] = {"file": str(path), "sha256": sha(path), "n": len(keep),
                                      "per_regulation": dict(sorted(per_reg.items())),
                                      "validation": (v.stdout or v.stderr).strip(), "valid": v.returncode == 0,
                                      "removed": removed, "added": added}
        print(f"{name:<12} n={len(keep):>3}  removed {len(removed):>2}  added {len(added):>2}  "
              f"valid={v.returncode == 0}  sha256={sha(path)[:16]}...")
        print("             per regulation:", dict(sorted(per_reg.items())))
    (OUT / "round3-change-ledger.json").write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"ledger: {OUT / 'round3-change-ledger.json'}")
    assert sha(BEST) == BEST_SHA


if __name__ == "__main__":
    main()
