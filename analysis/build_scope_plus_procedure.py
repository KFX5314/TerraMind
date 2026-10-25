"""Remove only seven repeated or procedural checks from the side-signal candidate."""

import hashlib
import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts/evaluations/heldout-f2-module-scope-20261025"
SOURCE = OUT / "module-side-signal-scope.json"
SOURCE_HASH = "d5b3d5b610bda96504a7aba5709aea3985194e834fbc7e5575ae2508f8a6c3fc"
TARGET = OUT / "module-side-signal-procedure-trim.json"
RAW = Path("C:/Users/saish/Certivity/TeraMind/TerraMind/artifacts/runs/heldout-v1/requirements.json")
REASONS = {
    "R-0780": "Annex 9 production-check procedure repeats lamp positioning requirements already exported from R48 section 5 and the applicable function section.",
    "R-0782": "Annex 9 production-check procedure repeats the visibility-angle requirement already exported from the applicable R48 function section.",
    "R-0783": "Annex 9 production-check procedure repeats the front/rear light-visibility restriction already exported as R48 section 5.10.",
    "R-0787": "Annex 9 instruction to check production electrical connections by switching lamps is an inspection action, not a distinct lamp-design constraint.",
    "R-0789": "Annex 9 instruction to inspect production lamps and markings visually repeats presence, colour, number and category obligations.",
    "R-1121": "Annex 4 statement about when mass-production photometric conformity shall not be contested is a sampling judgment, not an independently specified lamp performance limit.",
    "R-1129": "Annex 5 inspector-sampling statement about when photometric conformity shall not be contested is a sampling judgment, not an independently specified lamp performance limit.",
}

assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == SOURCE_HASH
source = json.loads(SOURCE.read_text(encoding="utf8"))
raw = {x["id"]: x for x in json.loads(RAW.read_text(encoding="utf8"))}
removed = []
kept = []
for item in source["requirements"]:
    ident = item["id"]
    if ident in REASONS:
        saved = raw[ident]
        removed.append({"id": ident, "text": item["text"], "source": item["source"],
                        "source_quote": saved["quote"], "reason": REASONS[ident]})
    else:
        kept.append(item)
assert len(removed) == 7 and len(kept) == 367
result = {"team_id": source["team_id"], "case_id": source["case_id"], "requirements": kept}
data = (json.dumps(result, ensure_ascii=False, indent=2) + "\n").encode("utf8")
with TARGET.open("xb") as handle:
    handle.write(data)
TARGET.chmod(0o444)
ledger = {"parent": str(SOURCE), "parent_sha256": SOURCE_HASH,
          "target": str(TARGET), "target_sha256": hashlib.sha256(data).hexdigest(),
          "count": len(kept), "by_regulation": dict(Counter(x["source"]["regulation"] for x in kept)),
          "removed_vs_parent": removed}
(OUT / "procedure-trim-ledger.json").write_text(json.dumps(ledger, ensure_ascii=False, indent=2) + "\n", encoding="utf8")
print(TARGET, len(kept), hashlib.sha256(data).hexdigest())
