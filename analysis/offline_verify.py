"""Read-only verification of saved held-out submissions; no model or network calls."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EVAL = ROOT / "artifacts" / "evaluations"
SCORED = EVAL / "heldout-f2-offline-alternatives-20261025" / "eval-balanced-source-faithful.json"
FILES = {
    "scored-450": (SCORED, 450, "9c4cbac94ffe34f6ac031744f277d1aade0ce46153f648b2a4d4175725b6b936"),
    "intermediate-438": (EVAL / "heldout-f2-independent-20261025" / "verified-intermediate-438.json", 438, "5e336e65e02b1211308c09a2a67dab7e485569a308bdc7459172f3cba92da30f"),
    "module-360": (EVAL / "heldout-f2-module-scope-20261025" / "module-evidence-side-recovery-360.json", 360, "02500e7caaab14aa63bd7ee3a0e509f557a781b4f6aeb34c98005af6b4931a5b"),
}


def main() -> None:
    docs = {}
    for label, (path, count, expected_hash) in FILES.items():
        raw = path.read_bytes()
        digest = hashlib.sha256(raw).hexdigest()
        assert digest == expected_hash, f"{label}: unexpected SHA-256 {digest}"
        doc = json.loads(raw)
        rows = doc["requirements"]
        assert doc["case_id"] == "heldout-front-bumper"
        assert len(rows) == count
        assert len({row["id"] for row in rows}) == count
        docs[label] = {row["id"] for row in rows}
        print(f"{label}: {count} requirements, SHA-256 {digest}")
    base = docs["scored-450"]
    for label in ("intermediate-438", "module-360"):
        ids = docs[label]
        print(f"{label} versus scored: +{len(ids - base)} / -{len(base - ids)} requirements")


if __name__ == "__main__":
    main()
