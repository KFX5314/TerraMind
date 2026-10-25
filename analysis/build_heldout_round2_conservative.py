"""Conservative offline pruning from the scored 479-item held-out upload."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FIRST = ROOT / "artifacts/evaluations/heldout-f2-20261025"
SECOND = ROOT / "artifacts/evaluations/heldout-f2-round2-20261025"
OUT = ROOT / "artifacts/evaluations/heldout-f2-conservative-20261025"
SAVED = Path("C:/Users/saish/Certivity/TeraMind/TerraMind/artifacts/runs/heldout-v1")
FUNCTIONS = {
    "6.3": "No front fog lamp is specified or labelled in the product drawing.",
    "6.16": "No front retro-reflector is specified or labelled in the product drawing.",
    "6.17": "No side retro-reflector is specified or labelled in the product drawing.",
    "6.20": "No cornering lamp is specified or labelled in the product drawing.",
    "6.26": "No manoeuvring lamp is specified or labelled in the product drawing.",
}


def save_new(path: Path, data: bytes) -> None:
    with path.open("xb") as handle:
        handle.write(data)


def main() -> None:
    baseline_bytes = (SECOND / "scored-479.json").read_bytes()
    assert hashlib.sha256(baseline_bytes).hexdigest() == "7d97af7fbececfdba7d5e12f878b023eaab66b7c42ccfb132cc05585098232f2"
    baseline = json.loads(baseline_bytes)
    extracted = {x["id"]: x for x in json.loads((SAVED / "requirements.json").read_text(encoding="utf8"))}
    keep = []
    removed = []
    counts = Counter()
    for item in baseline["requirements"]:
        reg = item["source"]["regulation"]
        para = item["source"].get("paragraph", "")
        group = next((k for k in FUNCTIONS if reg == "UN R48" and (para == k or para.startswith(k + "."))), None)
        if group is None:
            keep.append(item)
        else:
            counts[group] += 1
            old = extracted[item["id"]]
            removed.append({"id": item["id"], "source": item["source"], "text": item["text"],
                            "reason": FUNCTIONS[group], "saved_probability": old["probability"],
                            "saved_applicability": old["applicability"], "saved_condition": old.get("condition", "")})
    assert counts == Counter({"6.3": 9, "6.16": 7, "6.17": 6, "6.20": 11, "6.26": 6})
    assert len(keep) == 440
    x = extracted["R-0894"]
    assert x["paragraph"] == "Annex 5 1.10" and x["page"] == 33 and not x["exported"]
    added = {"id": x["id"], "text": x["text"],
             "source": {key: x[key] for key in ("regulation", "version", "page", "paragraph")},
             "test_case": x["test_case"]}
    OUT.mkdir(parents=True, exist_ok=False)
    save_new(OUT / "scored-479.json", baseline_bytes)
    for name, requirements in (("feature-scope-440", keep), ("focused-recovery-441", keep + [added])):
        doc = {"team_id": baseline["team_id"], "case_id": baseline["case_id"], "requirements": requirements}
        save_new(OUT / f"{name}.json", (json.dumps(doc, ensure_ascii=False, indent=2) + "\n").encode("utf8"))
        print(name, len(requirements), hashlib.sha256((OUT / f"{name}.json").read_bytes()).hexdigest())
    (OUT / "change-ledger.json").write_text(json.dumps({
        "baseline": "officially scored 479-item upload, F2 59.1%, recall 74.5%, precision 32.4%",
        "baseline_sha256": hashlib.sha256(baseline_bytes).hexdigest(),
        "removed": removed,
        "added_to_focused_recovery": [{"id": added["id"], "source": added["source"], "text": added["text"],
                                        "quote": x["quote"], "probability": x["probability"],
                                        "reason": "R127 lower-legform impact test has a distinct ±10 mm horizontal and vertical tolerance; source quote verified on PDF page 33."}],
        "counts": {"removed": len(removed), "added": 1, "feature_scope": 440, "focused_recovery": 441},
        "removed_by_function": dict(counts),
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf8")


if __name__ == "__main__":
    main()
