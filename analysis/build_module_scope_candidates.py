"""Offline front-bumper module-scope alternatives from the scored 450-item JSON."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts/evaluations/heldout-f2-module-scope-20261025"
SOURCE = ROOT / "artifacts/evaluations/heldout-f2-offline-alternatives-20261025/eval-balanced-source-faithful.json"
RAW = Path("C:/Users/saish/Certivity/TeraMind/TerraMind/artifacts/runs/heldout-v1/requirements.json")
SOURCE_HASH = "9c4cbac94ffe34f6ac031744f277d1aade0ce46153f648b2a4d4175725b6b936"

CORE_R48 = {
    "6.16": "No front retro-reflector is identified on the bumper; the saved screen also excluded reflector-device regulation R3 for this reason.",
    "6.17": "No side retro-reflector is identified on the bumper; the saved screen also excluded reflector-device regulation R3 for this reason.",
    "6.9": "A front position lamp is mandatory for the vehicle but is not identified as a component of this bumper module.",
    "6.19": "A daytime-running lamp is mandatory for the vehicle but is not identified as a component of this bumper module.",
}
CORE_R148 = {
    "5.1": "This front-position/end-outline lamp photometry applies only if the bumper carries that unlisted lamp function.",
    "5.4": "This daytime-running-lamp photometry applies only if the bumper carries that unlisted lamp function.",
    "Annex 6": "This daytime-running-lamp heat test applies only if the bumper carries that unlisted lamp function.",
}
CORE_IDS = {
    "R-1106": "Front-position lamp Annex 2 visibility is conditional on an unlisted module function.",
    "R-1107": "Daytime-running lamp Annex 2 visibility is conditional on an unlisted module function.",
    "R-0938": "This handed-marking variant is specific to unlisted front/rear position or end-outline lamps; general lamp markings remain.",
}
SIDE_R48 = {
    "R-0555", "R-0556", "R-0557", "R-0562", "R-0563", "R-0566", "R-0573", "R-0574"
}
SIDE_R148 = {"R-0937", "R-1054", "R-1056", "R-1057", "R-1058", "R-1066", "R-1067", "R-1068", "R-1069", "R-1070", "R-1071", "R-1101"}


def para_in(para: str, root: str) -> bool:
    return para == root or para.startswith(root + ".") or para.startswith(root + " ")


def scope_reason(item: dict, side_only: bool = False) -> str | None:
    src = item["source"]
    reg, para, ident = src["regulation"], src["paragraph"], item["id"]
    if reg == "UN R48":
        for root, reason in CORE_R48.items():
            if para_in(para, root):
                return reason
    if reg == "UN R148":
        for root, reason in CORE_R148.items():
            if para_in(para, root):
                return reason
        if ident in CORE_IDS:
            return CORE_IDS[ident]
    if side_only and ((reg == "UN R48" and ident in SIDE_R48) or
                      (reg == "UN R148" and ident in SIDE_R148)):
        return "The saved applicability condition requires a front direction-indicator variant, while the identified bumper lighting is side signalling; side-indicator and general marking duties remain."
    return None


def make_candidate(name: str, source: dict, raw: dict, side_only: bool) -> dict:
    kept = []
    removed = []
    for item in source["requirements"]:
        reason = scope_reason(item, side_only)
        if reason is None:
            kept.append(item)
            continue
        saved = raw[item["id"]]
        removed.append({
            "id": item["id"], "text": item["text"], "source": item["source"],
            "source_quote": saved["quote"],
            "saved_probability": saved["probability"],
            "saved_applicability": saved["applicability"],
            "saved_condition": saved.get("condition", ""), "reason": reason,
        })
    result = {"team_id": source["team_id"], "case_id": source["case_id"], "requirements": kept}
    data = (json.dumps(result, ensure_ascii=False, indent=2) + "\n").encode("utf8")
    path = OUT / name
    with path.open("xb") as handle:
        handle.write(data)
    path.chmod(0o444)
    return {"filename": name, "count": len(kept), "by_regulation": dict(Counter(x["source"]["regulation"] for x in kept)),
            "sha256": hashlib.sha256(data).hexdigest(), "removed": removed, "added": [], "modified": []}


def main() -> None:
    content = SOURCE.read_bytes()
    assert hashlib.sha256(content).hexdigest() == SOURCE_HASH
    source = json.loads(content)
    assert len(source["requirements"]) == 450
    raw = {x["id"]: x for x in json.loads(RAW.read_text(encoding="utf8"))}
    OUT.mkdir(parents=True, exist_ok=False)
    candidates = {
        "module-lamp-scope": make_candidate("module-lamp-scope.json", source, raw, False),
        "module-side-signal-scope": make_candidate("module-side-signal-scope.json", source, raw, True),
    }
    ledger = {"scored_baseline": str(SOURCE), "scored_f2": 61.2, "baseline_sha256": SOURCE_HASH,
              "candidates": candidates,
              "limits": "Missing hardware is inferred from the supplied module spec/drawing, not a complete vehicle bill of materials; hidden labels are unavailable."}
    (OUT / "change-ledger.json").write_text(json.dumps(ledger, ensure_ascii=False, indent=2) + "\n", encoding="utf8")
    for name, item in candidates.items():
        print(name, item["count"], "removed", len(item["removed"]), item["sha256"])


if __name__ == "__main__":
    main()
