"""Add two source-checked side-indicator obligations to the scoped 358 JSON."""

import hashlib
import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DIR = ROOT / "artifacts/evaluations/heldout-f2-module-scope-20261025"
SOURCE = DIR / "module-evidence-358.json"
SOURCE_HASH = "ce5f24b5fdbe3ab9281d89c11fcce07f85659e64a4c1e3b5a8c322dbb7a7bf1f"
RECOVERY = ROOT / "artifacts/evaluations/heldout-f2-offline-alternatives-20261025/eval-high-recall.json"
RAW = Path("C:/Users/saish/Certivity/TeraMind/TerraMind/artifacts/runs/heldout-v1/requirements.json")
TARGET = DIR / "module-evidence-side-recovery-360.json"
IDS = {"R-0940", "R-1152"}

assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == SOURCE_HASH
source = json.loads(SOURCE.read_text(encoding="utf8"))
saved = {x["id"]: x for x in json.loads(RAW.read_text(encoding="utf8"))}
recovered = {x["id"]: x for x in json.loads(RECOVERY.read_text(encoding="utf8"))["requirements"] if x["id"] in IDS}
assert set(recovered) == IDS
assert not IDS.intersection(x["id"] for x in source["requirements"])
adds = []
for ident in sorted(IDS):
    item = recovered[ident]
    assert item["source"]["regulation"] == "UN R148"
    original = saved[ident]
    adds.append({"id": ident, "text": item["text"], "source": item["source"],
                 "source_quote": original["quote"], "saved_probability": original["probability"],
                 "saved_condition": original["condition"],
                 "reason": ("Category-6 side direction indicator R/L marking is mandatory when that lamp category is installed."
                            if ident == "R-0940" else
                            "Annex 8 Table A8-1 requires a category-5/6 side-indicator check 0.2 s after switch-on at H5,V0 when that lamp category is installed.")})
doc = {"team_id": source["team_id"], "case_id": source["case_id"],
       "requirements": source["requirements"] + [recovered[i] for i in sorted(IDS)]}
assert len(doc["requirements"]) == 360
data = (json.dumps(doc, ensure_ascii=False, indent=2) + "\n").encode("utf8")
with TARGET.open("xb") as handle:
    handle.write(data)
TARGET.chmod(0o444)
(DIR / "module-recovery-360-ledger.json").write_text(json.dumps({
    "parent": str(SOURCE), "parent_sha256": SOURCE_HASH, "target": str(TARGET),
    "target_sha256": hashlib.sha256(data).hexdigest(), "count": 360,
    "by_regulation": dict(Counter(x["source"]["regulation"] for x in doc["requirements"])),
    "added_vs_parent": adds,
    "risk": "Both duties are conditional on the side-indicator category; the supplied product specification does not identify the category.",
}, ensure_ascii=False, indent=2) + "\n", encoding="utf8")
print(TARGET, 360, hashlib.sha256(data).hexdigest())
