"""Create an immutable source-faithful variant of the balanced held-out JSON."""

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts/evaluations/heldout-f2-offline-alternatives-20261025"
SOURCE = OUT / "eval-balanced.json"
TARGET = OUT / "eval-balanced-source-faithful.json"
LEDGER = OUT / "balanced-source-faithful-ledger.json"

assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == "27c44519ebe72e22ffe8638c538c855d8cf5a8ff1baa6033b720738134b2f9c6"
doc = json.loads(SOURCE.read_text(encoding="utf8"))
assert len(doc["requirements"]) == 450

changes = {}
for item in doc["requirements"]:
    if item["id"] not in {"R-0414", "R-0420"}:
        continue
    before = item["text"]
    after = before.replace(" shall be impacted ", " should be impacted ")
    assert before != after
    item["text"] = after
    changes[item["id"]] = {
        "before": before,
        "after": after,
        "source": item["source"],
        "reason": "The cited UN R42 impact-test procedure says 'should', not 'shall'; preserve the numerical speed and tolerance.",
    }
assert len(changes) == 2

data = (json.dumps(doc, ensure_ascii=False, indent=2) + "\n").encode("utf8")
with TARGET.open("xb") as handle:
    handle.write(data)
LEDGER.write_text(json.dumps({
    "parent": SOURCE.name,
    "parent_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
    "target": TARGET.name,
    "target_sha256": hashlib.sha256(data).hexdigest(),
    "changes": changes,
}, ensure_ascii=False, indent=2) + "\n", encoding="utf8")
TARGET.chmod(0o444)
print(TARGET, len(doc["requirements"]), hashlib.sha256(data).hexdigest())
