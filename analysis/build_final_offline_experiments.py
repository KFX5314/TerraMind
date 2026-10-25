"""Build isolated, source-reviewed held-out experiments from cached artifacts only."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "artifacts/evaluations/heldout-f2-offline-alternatives-20261025/eval-balanced-source-faithful.json"
RAW = ROOT.parent / "TeraMind/TerraMind/artifacts/runs/heldout-v1/requirements.json"
OUT = ROOT / "artifacts/evaluations/heldout-final-offline-20261025"

# All are source-supported and previously filtered. Charging-ESA entries are
# conditional on an ESA in the bumper taking part in grid-connected charging.
RECOVER = [
    "R-0362", "R-0368", "R-0708",  # air flap, aerial cap, M1 marking ban
    "R-0053", "R-0126", "R-0127", "R-0128", "R-0129", "R-0130",
    "R-0132", "R-0133", "R-0135", "R-0136", "R-0140", "R-0142", "R-0143",
]
CHARGING = set(RECOVER[3:])
REMOVE_REDUNDANT = ["R-0023", "R-0027"]


def dump_new(path: Path, value: object) -> str:
    data = (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    with path.open("xb") as file:
        file.write(data)
    return hashlib.sha256(data).hexdigest()


def add_recoveries(sub: dict, raw: dict[str, dict], changes: list[dict]) -> None:
    for identifier in RECOVER:
        c = raw[identifier]
        text = c["text"]
        if identifier in CHARGING and "REESS charging mode" not in text:
            text = "For an ESA operating in REESS charging mode coupled to the power grid, " + text[0].lower() + text[1:]
        item = {
            "id": identifier,
            "text": text,
            "source": {"regulation": c["regulation"], "version": c["version"],
                       "page": c["page"], "paragraph": c["paragraph"]},
        }
        if c.get("test_case"):
            item["test_case"] = c["test_case"]
        sub["requirements"].append(item)
        changes.append({"action": "add", "id": identifier, "regulation": c["regulation"],
                        "source_page": c["page"], "source_paragraph": c["paragraph"],
                        "saved_probability": c["probability"], "saved_condition": c.get("condition", ""),
                        "source_quote": c.get("quote", ""),
                        "reason": "Previously filtered independent clause; applicable under the stated product configuration."})


def normalize(sub: dict, changes: list[dict]) -> None:
    by_id = {x["id"]: x for x in sub["requirements"]}
    # PDF page 3, R42 6.1.1 has two independently inspectable post-impact outcomes.
    old = by_id["R-0380"]
    replacements = [
        ("N-R42-0380-OPERATE",
         "After each impact test made in accordance with Annex 3, the lighting and signalling devices shall continue to operate correctly, except that disturbed factory-fitted lighting adjustment may be corrected by normal means and bulbs may be replaced after filament failure.",
         "Check operation of each lighting and signalling device after the Annex 3 impact, allowing the source-stated adjustment and bulb exceptions."),
        ("N-R42-0380-VISIBLE",
         "After each impact test made in accordance with Annex 3, the lighting and signalling devices shall remain visible.",
         "Inspect whether each lighting and signalling device remains visible after the Annex 3 impact."),
    ]
    sub["requirements"].remove(old)
    changes.append({"action": "replace", "id": old["id"], "reason": "Separate operation from visibility; both are explicit in R42 6.1.1 PDF page 3.",
                    "original": old})
    for identifier, text, test_case in replacements:
        sub["requirements"].append({"id": identifier, "text": text,
            "source": copy.deepcopy(old["source"]), "test_case": test_case})
        changes.append({"action": "add_split", "id": identifier, "from": old["id"],
                        "source_page": 3, "source_paragraph": "6.1.1"})

    # R42 6.1.3 separately tests fluid leakage and passage constriction.
    old = by_id["R-0383"]
    replacements = [
        ("N-R42-0383-LEAK",
         "After each impact test made in accordance with Annex 3, the vehicle's fuel and cooling systems shall have no leaks.",
         "Inspect fuel and cooling systems for leaks after each Annex 3 impact."),
        ("N-R42-0383-FLOW",
         "After each impact test made in accordance with Annex 3, the vehicle's fuel and cooling systems shall have no constricted fluid passages that prevent normal functioning.",
         "Check whether fuel and cooling passages remain clear enough for normal functioning after each Annex 3 impact."),
    ]
    sub["requirements"].remove(old)
    changes.append({"action": "replace", "id": old["id"], "reason": "Separate leakage from passage constriction; both are explicit in R42 6.1.3 PDF page 3.",
                    "original": old})
    for identifier, text, test_case in replacements:
        sub["requirements"].append({"id": identifier, "text": text,
            "source": copy.deepcopy(old["source"]), "test_case": test_case})
        changes.append({"action": "add_split", "id": identifier, "from": old["id"],
                        "source_page": 3, "source_paragraph": "6.1.3"})

    # These bumper-height branches are in the lead-in 5.1, not 5.1.1.
    for identifier in ("R-0864", "R-0865"):
        item = by_id[identifier]
        prior = item["source"]["paragraph"]
        item["source"]["paragraph"] = "5.1"
        changes.append({"action": "correct_citation", "id": identifier,
                        "before": prior, "after": "5.1", "source_page": 18,
                        "reason": "PDF page 18 places the bumper-height selection branches in paragraph 5.1."})


def remove_redundancy(sub: dict, changes: list[dict]) -> None:
    for identifier in REMOVE_REDUNDANT:
        item = next(x for x in sub["requirements"] if x["id"] == identifier)
        sub["requirements"].remove(item)
        counterpart = {"R-0023": "R-0161", "R-0027": "R-0164"}[identifier]
        changes.append({"action": "remove_equivalent", "id": identifier,
                        "retained_id": counterpart, "original": item,
                        "reason": "Same ESA, frequency band and 63/53 dBµV/m limit in R10 6.5.2.1/6.6.2.1 and Appendix 6/7; retained appendix entry includes bandwidth."})


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    baseline_bytes = BASE.read_bytes()
    baseline_hash = hashlib.sha256(baseline_bytes).hexdigest()
    baseline = json.loads(baseline_bytes)
    raw = {x["id"]: x for x in json.loads(RAW.read_text(encoding="utf-8"))}
    plans = {
        "A-high-recall-466.json": [add_recoveries],
        "B-atomic-normalization-452.json": [normalize],
        "C-exact-redundancy-448.json": [remove_redundancy],
        "AB-combined-468.json": [add_recoveries, normalize],
    }
    for name, operations in plans.items():
        sub = copy.deepcopy(baseline)
        changes: list[dict] = []
        for op in operations:
            if op is add_recoveries:
                op(sub, raw, changes)
            else:
                op(sub, changes)
        ids = [x["id"] for x in sub["requirements"]]
        assert len(ids) == len(set(ids)), name
        count = int(name.split("-")[-1].split(".")[0])
        assert len(ids) == count, (name, len(ids))
        digest = dump_new(OUT / name, sub)
        dump_new(OUT / name.replace(".json", "-ledger.json"), {
            "baseline": str(BASE), "baseline_sha256": baseline_hash,
            "candidate": str(OUT / name), "candidate_sha256": digest,
            "count": count, "changes": changes,
        })
        print(name, count, digest, "changes", len(changes))
    assert hashlib.sha256(BASE.read_bytes()).hexdigest() == baseline_hash


if __name__ == "__main__":
    main()
