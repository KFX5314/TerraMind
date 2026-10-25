"""Finish explicit module-function exclusions while retaining the R94 crash criteria."""

import hashlib
import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts/evaluations/heldout-f2-module-scope-20261025"
SOURCE = OUT / "module-side-signal-procedure-trim.json"
SOURCE_HASH = "3475760bfd7fd9f51f8c8fed0f2bc98a8b0f155ae938a6622091dc2053cd65a5"
TARGET = OUT / "module-evidence-358.json"
RAW = Path("C:/Users/saish/Certivity/TeraMind/TerraMind/artifacts/runs/heldout-v1/requirements.json")
REASONS = {
    "R-0467": "Front-position lamp colour applies to a lamp function not identified in the bumper module; the side lamp colour rule remains.",
    "R-0472": "Daytime-running lamp colour applies to a lamp function not identified in the bumper module; the side lamp colour rule remains.",
    "R-0572": "The source explicitly exempts side direction indicators of categories 5 and 6 from this apparent-surface criterion; only side signalling is identified.",
    "R-1115": "The listed photometric categories are front/rear position, parking, stop and front/rear direction indicators, not side categories 5/6 or side-marker lamps.",
    "R-0877": "The optional active ride-height suspension system (ARHSS) is not identified in the vehicle or bumper specification.",
    "R-0891": "A pedestrian-impact sensor is listed, but no active or deployable pedestrian-protection device is identified; the obligation is conditional on such a device.",
    "R-0892": "A pedestrian-impact sensor is listed, but no active or deployable pedestrian-protection device is identified; the obligation is conditional on such a device.",
    "R-1194": "GTR9 active-device test condition is conditional on a deployable protection device, which is not identified; passive bumper and impact-test duties remain.",
    "R-0361": "The supplied 'fuel filler cap' is explicitly for EVs and denotes a charging flap, not a liquid-fuel tank filler cap governed by this R26 clause.",
}

assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == SOURCE_HASH
source = json.loads(SOURCE.read_text(encoding="utf8"))
raw = {x["id"]: x for x in json.loads(RAW.read_text(encoding="utf8"))}
removed, kept = [], []
for item in source["requirements"]:
    ident = item["id"]
    if ident not in REASONS:
        kept.append(item)
        continue
    saved = raw[ident]
    removed.append({"id": ident, "text": item["text"], "source": item["source"],
                    "source_quote": saved["quote"], "saved_probability": saved["probability"],
                    "saved_applicability": saved["applicability"],
                    "saved_condition": saved.get("condition", ""), "reason": REASONS[ident]})
assert len(removed) == 9 and len(kept) == 358
result = {"team_id": source["team_id"], "case_id": source["case_id"], "requirements": kept}
data = (json.dumps(result, ensure_ascii=False, indent=2) + "\n").encode("utf8")
with TARGET.open("xb") as handle:
    handle.write(data)
TARGET.chmod(0o444)
(OUT / "module-evidence-358-ledger.json").write_text(json.dumps({
    "parent": str(SOURCE), "parent_sha256": SOURCE_HASH, "target": str(TARGET),
    "target_sha256": hashlib.sha256(data).hexdigest(), "count": len(kept),
    "by_regulation": dict(Counter(x["source"]["regulation"] for x in kept)),
    "removed_vs_parent": removed, "risk": "Product spec may omit optional hardware present in the intended vehicle; official gold matching is unknown.",
}, ensure_ascii=False, indent=2) + "\n", encoding="utf8")
print(TARGET, len(kept), hashlib.sha256(data).hexdigest())
