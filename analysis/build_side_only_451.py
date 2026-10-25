"""Conservative side-signal recovery from the source-checked 449 JSON."""

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts/evaluations/heldout-f2-post438-20261025"
SOURCE = OUT / "source-corrected-449.json"
SOURCE_SHA = "296d63e9d40dd51390d8f07d7f677213615eec397b54a5efd8b788798ae67699"
RECOVERY = OUT / "targeted-recovery-452.json"
RECOVERY_SHA = "f10e7f39e10a3439ce564659d20d799d50d0176668c08274a0ab2d7819322383"
TARGET = OUT / "side-signal-recovery-451.json"
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == SOURCE_SHA
assert hashlib.sha256(RECOVERY.read_bytes()).hexdigest() == RECOVERY_SHA
base = json.loads(SOURCE.read_text(encoding="utf8"))
adds = {x["id"]: x for x in json.loads(RECOVERY.read_text(encoding="utf8"))["requirements"] if x["id"] in {"R-0940", "R-1152"}}
assert set(adds) == {"R-0940", "R-1152"}
assert not set(adds) & {x["id"] for x in base["requirements"]}
doc = {"team_id": base["team_id"], "case_id": base["case_id"],
       "requirements": base["requirements"] + [adds[i] for i in sorted(adds)]}
assert len(doc["requirements"]) == 451
data = (json.dumps(doc, ensure_ascii=False, indent=2) + "\n").encode("utf8")
with TARGET.open("xb") as handle:
    handle.write(data)
TARGET.chmod(0o444)
(OUT / "side-signal-451-ledger.json").write_text(json.dumps({
    "parent": str(SOURCE), "parent_sha256": SOURCE_SHA,
    "target": str(TARGET), "target_sha256": hashlib.sha256(data).hexdigest(),
    "added": [adds[i] for i in sorted(adds)],
    "reason": "Restore only saved R148 duties for the explicitly drawn side signalling lamp; leave uncertain active grille-shutter requirement out.",
}, ensure_ascii=False, indent=2) + "\n", encoding="utf8")
print(TARGET, len(doc["requirements"]), hashlib.sha256(data).hexdigest())
