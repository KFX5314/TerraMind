"""Optional high-risk system-boundary variant; keeps all other scoped obligations."""

import hashlib
import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts/evaluations/heldout-f2-module-scope-20261025"
SOURCE = OUT / "module-side-signal-procedure-trim.json"
SOURCE_HASH = "3475760bfd7fd9f51f8c8fed0f2bc98a8b0f155ae938a6622091dc2053cd65a5"
TARGET = OUT / "module-system-boundary.json"
RAW = Path("C:/Users/saish/Certivity/TeraMind/TerraMind/artifacts/runs/heldout-v1/requirements.json")

REMOVE = {"R-0790", *(f"R-{n:04d}" for n in range(795, 805)), "R-0361"}
assert len(REMOVE) == 12
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == SOURCE_HASH
source = json.loads(SOURCE.read_text(encoding="utf8"))
raw = {x["id"]: x for x in json.loads(RAW.read_text(encoding="utf8"))}
removed, kept = [], []
for item in source["requirements"]:
    ident = item["id"]
    if ident not in REMOVE:
        kept.append(item)
        continue
    reason = ("R94 front-occupant injury criteria are measured on seated dummies in a full-vehicle impact; no restraint or passenger compartment is part of the supplied bumper module. This is a system-boundary inference, not proof the criterion is absent from hidden gold."
              if item["source"]["regulation"] == "UN R94" else
              "The product specification describes a charging flap for an EV, not a liquid-fuel tank filler cap; the R26 fuel-filler projection rule addresses a different component.")
    saved = raw[ident]
    removed.append({"id": ident, "text": item["text"], "source": item["source"],
                    "source_quote": saved["quote"], "saved_probability": saved["probability"],
                    "reason": reason})
assert len(removed) == 12 and len(kept) == 355
result = {"team_id": source["team_id"], "case_id": source["case_id"], "requirements": kept}
data = (json.dumps(result, ensure_ascii=False, indent=2) + "\n").encode("utf8")
with TARGET.open("xb") as handle:
    handle.write(data)
TARGET.chmod(0o444)
(OUT / "system-boundary-ledger.json").write_text(json.dumps({
    "parent": str(SOURCE), "parent_sha256": SOURCE_HASH, "target": str(TARGET),
    "target_sha256": hashlib.sha256(data).hexdigest(), "count": len(kept),
    "by_regulation": dict(Counter(x["source"]["regulation"] for x in kept)),
    "removed_vs_parent": removed,
    "risk": "High: full-vehicle occupant outcomes may be counted as relevant because the bumper influences frontal crash energy management.",
}, ensure_ascii=False, indent=2) + "\n", encoding="utf8")
print(TARGET, len(kept), hashlib.sha256(data).hexdigest())
