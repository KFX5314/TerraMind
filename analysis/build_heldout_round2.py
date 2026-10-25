"""Build offline scope-screened candidates from the officially scored 479-item file.

No model calls, no mutation of saved submissions, and exclusive file creation.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PREVIOUS = ROOT / "artifacts/evaluations/heldout-f2-20261025"
OUT = ROOT / "artifacts/evaluations/heldout-f2-round2-20261025"
SAVED = Path("C:/Users/saish/Certivity/TeraMind/TerraMind/artifacts/runs/heldout-v1")

UNCONFIRMED_R48 = {
    "6.3": "Front fog lamps are not named or shown in the bumper specification; 'functional' lighting has no identified part.",
    "6.16": "Front retro-reflectors are not named or shown in the bumper specification or drawing.",
    "6.17": "Side retro-reflectors are not named or shown in the bumper specification or drawing.",
    "6.20": "Cornering lamps are not named or shown in the bumper specification or drawing.",
    "6.26": "Manoeuvring lamps are not named or shown in the bumper specification or drawing.",
    "6.27": "An optical answer-back function is not stated; the keyless aerial alone does not establish one.",
}

LAB_ONLY_R10 = {
    "R-0222", "R-0223", "R-0226", "R-0233", "R-0277", "R-0279", "R-0280",
    "R-0282", "R-0283", "R-0284", "R-0285",
}

PROCEDURE_R148 = {
    "R-0995", "R-1028", "R-1031", "R-1091", "R-1092", "R-1122", "R-1130",
}

RECOVER_R127 = {"R-0902", "R-0904", "R-0908", "R-0909", "R-0910"}


def write_new(path: Path, value: bytes) -> None:
    with path.open("xb") as handle:
        handle.write(value)


def main() -> None:
    scored_bytes = (PREVIOUS / "verified-recovery.json").read_bytes()
    assert hashlib.sha256(scored_bytes).hexdigest() == "7d97af7fbececfdba7d5e12f878b023eaab66b7c42ccfb132cc05585098232f2"
    scored = json.loads(scored_bytes)
    assert len(scored["requirements"]) == 479
    extracted = {x["id"]: x for x in json.loads((SAVED / "requirements.json").read_text(encoding="utf8"))}
    recall = json.loads((PREVIOUS / "recall-recovery.json").read_text(encoding="utf8"))
    recall_by_id = {x["id"]: x for x in recall["requirements"]}
    removed = []
    kept = []
    counts = Counter()
    for item in scored["requirements"]:
        ident = item["id"]
        reg = item["source"]["regulation"]
        para = item["source"].get("paragraph", "")
        reason = None
        if reg == "UN R48":
            for prefix, why in UNCONFIRMED_R48.items():
                if para == prefix or para.startswith(prefix + "."):
                    reason = why
                    counts[f"R48 {prefix}"] += 1
                    break
        elif reg == "UN R10" and ident in LAB_ONLY_R10:
            reason = "Detailed laboratory setup or measurement-quality step, rather than a design/performance limit on the bumper ESA."
            counts["R10 lab procedure"] += 1
        elif reg == "UN R148" and ident in PROCEDURE_R148:
            reason = "Approval sampling, retest, or generic measurement procedure; no distinct device performance limit."
            counts["R148 procedure"] += 1
        if reason:
            old = extracted[ident]
            removed.append({"id": ident, "regulation": reg, "paragraph": para, "text": item["text"],
                            "reason": reason, "saved_probability": old["probability"],
                            "saved_applicability": old["applicability"], "saved_condition": old.get("condition", ""),
                            "source": item["source"]})
        else:
            kept.append(item)
    assert len(removed) == 61, dict(counts)
    assert counts == Counter({"R48 6.3": 9, "R48 6.16": 7, "R48 6.17": 6,
                              "R48 6.20": 11, "R48 6.26": 6, "R48 6.27": 4,
                              "R10 lab procedure": 11, "R148 procedure": 7}), counts
    assert all(ident not in {x["id"] for x in kept} for ident in RECOVER_R127)
    added = [recall_by_id[ident] for ident in sorted(RECOVER_R127)]
    previous_ledger = json.loads((PREVIOUS / "change-ledger.json").read_text(encoding="utf8"))
    evidence = {x["id"]: x for x in previous_ledger["added"]}
    assert all(evidence[x["id"]]["quote_on_cited_pdf_page"] for x in added)
    OUT.mkdir(parents=True, exist_ok=False)
    write_new(OUT / "scored-479.json", scored_bytes)
    variants = {
        "scope-screened-418": kept,
        "balanced-423": kept + added,
    }
    for name, requirements in variants.items():
        document = {"team_id": scored["team_id"], "case_id": scored["case_id"], "requirements": requirements}
        write_new(OUT / f"{name}.json", (json.dumps(document, ensure_ascii=False, indent=2) + "\n").encode("utf8"))
    ledger = {
        "scored_baseline": "verified-recovery.json; official score reported by user: F2 59.1%, R 74.5%, P 32.4%",
        "scored_sha256": hashlib.sha256(scored_bytes).hexdigest(),
        "removal_policy": "Exclude only unconfirmed lamp/reflector functions and detailed lab/approval procedures. This is a scope judgment, not a hidden-gold match.",
        "removed": removed,
        "added_to_balanced": [evidence[x["id"]] for x in added],
        "counts": {"scored": 479, "removed": len(removed), "scope_screened": len(kept), "balanced": len(kept) + len(added)},
        "removal_groups": dict(counts),
        "by_regulation": {name: dict(Counter(x["source"]["regulation"] for x in requirements))
                          for name, requirements in variants.items()},
    }
    (OUT / "change-ledger.json").write_text(json.dumps(ledger, ensure_ascii=False, indent=2) + "\n", encoding="utf8")
    for name in ["scored-479", *variants]:
        path = OUT / f"{name}.json"
        print(name, len(json.loads(path.read_text(encoding="utf8"))["requirements"]),
              hashlib.sha256(path.read_bytes()).hexdigest())
    print("removed groups", dict(counts))


if __name__ == "__main__":
    main()
