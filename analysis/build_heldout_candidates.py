"""Offline, source-checked recovery candidates for the saved heldout-v1 run.

The scored-upload provenance is not recorded locally; do not upload a candidate
until the saved baseline hash is matched to the platform upload receipt.
"""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from collections import Counter
from pathlib import Path

import pymupdf


ROOT = Path(__file__).resolve().parents[1]
SAVED = Path("C:/Users/saish/Certivity/TeraMind/TerraMind/artifacts/runs/heldout-v1")
PACKAGE = Path("C:/Users/saish/Certivity/industrial-ai-hackathon")
OUT = ROOT / "artifacts/evaluations/heldout-f2-20261025"

VERIFIED = {
    "R-0399": "R42 low-speed impactor mass sets an independently testable bumper-test condition.",
    "R-0421": "R42 recovery time applies if the bumper protective device uses self-restoring material; the EPP absorber makes this plausible.",
    "R-0899": "R127 lower-legform test-point spacing is a distinct numerical test condition.",
    "R-0900": "R127 lower-legform tests must sample differing structures across the bumper area.",
    "R-0905": "R127 requires three upper-legform tests across middle and outer bumper thirds when upper-legform testing applies.",
    "R-0906": "R127 upper-legform tests must sample differing structures when that test applies.",
    "R-0907": "R127 upper-legform test-point spacing is distinct from lower-legform spacing and applies by bumper height.",
}

RECALL_EXTRA = {
    "R-0362": "R26 air-flap edge rules are relevant only if the grille has movable intake or outlet flaps; the spec does not confirm them.",
    "R-0368": "R26 aerial end-cap radius applies only to an exposed external aerial; the specified keyless aerial may be internal.",
    "R-0443": "R48 multipart signalling-lamp geometry applies only if the lamp has distinct apparent-surface parts.",
    "R-0581": "R48 mode switching rule applies only if a direction indicator supports static and sequential modes.",
    "R-0902": "R127 lower-legform impactor height is a 75 mm plus/minus 10 mm test condition; an equivalent GTR9 condition is already exported.",
    "R-0904": "R127 upper-legform measuring points must lie in the bumper test area; upper test is conditional on bumper height.",
    "R-0908": "R127 upper-legform impact direction and two-degree tolerance are independently testable; GTR9 has a similar exported condition.",
    "R-0909": "R127 upper-legform vertical centreline is constrained to the midpoint within 10 mm; GTR9 has a similar exported condition.",
    "R-0910": "R127 upper-legform lateral centreline must be within 10 mm of the selected point; GTR9 has a similar exported condition.",
    "R-0940": "R148 category-6 side indicator marking is mandatory if that category is fitted; exact category is unspecified.",
    "R-1152": "R148 category-5/6 side indicator photometry has a 0.2-second check; exact category is unspecified.",
}

PREFIXES = {
    "R-0362": "If the bumper grille has movable air intake or outlet flaps, ",
    "R-0368": "If an external keyless-entry aerial has an unattached end, ",
    "R-0443": "If a bumper signalling lamp has an apparent surface composed of two or more distinct parts, ",
    "R-0581": "If a bumper direction indicator supports static and sequential modes, ",
    "R-0904": "Where upper-legform-to-bumper testing applies based on lower bumper height, ",
    "R-0905": "Where upper-legform-to-bumper testing applies based on lower bumper height, ",
    "R-0906": "Where upper-legform-to-bumper testing applies based on lower bumper height, ",
    "R-0907": "Where upper-legform-to-bumper testing applies based on lower bumper height, ",
    "R-0908": "Where upper-legform-to-bumper testing applies based on lower bumper height, ",
    "R-0909": "Where upper-legform-to-bumper testing applies based on lower bumper height, ",
    "R-0910": "Where upper-legform-to-bumper testing applies based on lower bumper height, ",
    "R-0940": "If the side signalling lamp is a category 6 direction indicator, ",
    "R-1152": "If the side signalling lamp is a category 5 or 6 direction indicator, ",
}

MANUAL = [
    {
        "id": "H-R127-1-9",
        "text": "In the flexible lower-legform-to-bumper test, the impactor shall have its intended orientation about the vertical axis at first contact, within a yaw angle tolerance of ±5°.",
        "source": {"regulation": "UN R127", "version": "4.3.0", "page": 33, "paragraph": "Annex 5 1.9"},
        "quote": "At the time of first contact the impactor shall have the intended orientation about its vertical axis, for the correct operation of its knee joint, with a yaw angle tolerance of ±5° (see Figure 3).",
        "reason": "R127 Annex 5 1.9 is a distinct lower-legform impact condition absent from every saved extracted candidate.",
    },
    {
        "id": "H-R127-1-13",
        "text": "In the flexible lower-legform-to-bumper test, tibia bending moments shall not exceed ±15 Nm during the 30 ms immediately before impact.",
        "source": {"regulation": "UN R127", "version": "4.3.0", "page": 33, "paragraph": "Annex 5 1.13"},
        "quote": "The tibia bending moments shall not exceed +/- 15 Nm within an evaluation interval of 30 ms immediately prior to impact.",
        "reason": "R127 Annex 5 1.13 is a separate pre-impact validity limit absent from every saved extracted candidate.",
    },
]


def norm(value: str) -> str:
    value = unicodedata.normalize("NFKC", value).casefold().replace("−", "-").replace("±", "+/-")
    return " ".join(value.split())


def write_new(path: Path, data: bytes) -> None:
    with path.open("xb") as handle:
        handle.write(data)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=False)
    source_bytes = (SAVED / "submission.json").read_bytes()
    base = json.loads(source_bytes)
    candidates = {r["id"]: r for r in json.loads((SAVED / "requirements.json").read_text(encoding="utf-8"))}
    baseline_ids = {r["id"] for r in base["requirements"]}
    all_ids = VERIFIED.keys() | RECALL_EXTRA.keys()
    assert not (all_ids & baseline_ids)
    assert len(candidates) == 1281 and len(base["requirements"]) == 470

    evidence = []
    recovered = {}
    for ident in sorted(all_ids):
        item = candidates[ident]
        source = {key: item[key] for key in ("regulation", "version", "page", "paragraph")}
        body = item["text"]
        prefix = PREFIXES.get(ident, "")
        if prefix:
            body = prefix + body[0].lower() + body[1:]
        recovered[ident] = {"id": ident, "text": body, "source": source}
        if item.get("test_case"):
            recovered[ident]["test_case"] = item["test_case"]
        evidence.append({
            "id": ident, "candidate": "verified-recovery" if ident in VERIFIED else "recall-recovery only",
            "reason": VERIFIED.get(ident) or RECALL_EXTRA[ident], "probability": item["probability"],
            "applicability": item["applicability"], "model_condition": item.get("condition", ""),
            "original_text": item["text"], "submitted_text": body, "quote": item["quote"],
            "source": source,
        })
    for entry in MANUAL:
        recovered[entry["id"]] = {key: entry[key] for key in ("id", "text", "source")}
        evidence.append({"id": entry["id"], "candidate": "verified-recovery", "reason": entry["reason"],
                         "probability": None, "applicability": "source-reviewed", "model_condition": "",
                         "original_text": None, "submitted_text": entry["text"], "quote": entry["quote"],
                         "source": entry["source"]})

    docs = {}
    for row in evidence:
        src = row["source"]
        regulation = src["regulation"]
        pdf = PACKAGE / "regulations/pdf" / regulation.replace(" ", "_") / "base" / f"{regulation.replace(' ', '_')}_base.pdf"
        if regulation not in docs:
            docs[regulation] = pymupdf.open(pdf)
        doc = docs[regulation]
        assert 1 <= src["page"] <= len(doc), row["id"]
        page_text = doc[src["page"] - 1].get_text()
        row["source_pdf"] = str(pdf)
        row["quote_on_cited_pdf_page"] = norm(row["quote"]) in norm(page_text)
        assert row["quote_on_cited_pdf_page"], row["id"]

    def candidate(add_ids: set[str]) -> dict:
        return {"team_id": base["team_id"], "case_id": base["case_id"],
                "requirements": base["requirements"] + [recovered[ident] for ident in sorted(add_ids)]}

    verified_ids = set(VERIFIED) | {x["id"] for x in MANUAL}
    recall_ids = verified_ids | set(RECALL_EXTRA)
    write_new(OUT / "baseline.json", source_bytes)
    for name, ids in (("verified-recovery", verified_ids), ("recall-recovery", recall_ids)):
        write_new(OUT / f"{name}.json", (json.dumps(candidate(ids), ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    (OUT / "change-ledger.json").write_text(json.dumps({
        "baseline_provenance": "heldout-v1 saved run; official upload attribution is unverified",
        "baseline_sha256": hashlib.sha256(source_bytes).hexdigest(),
        "added": evidence, "removed": [],
        "counts": {"baseline": len(base["requirements"]), "verified-recovery": 470 + len(verified_ids),
                   "recall-recovery": 470 + len(recall_ids)},
        "by_regulation": {name: dict(Counter(x["source"]["regulation"] for x in candidate(ids)["requirements"]))
                          for name, ids in (("verified-recovery", verified_ids), ("recall-recovery", recall_ids))},
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(str(OUT))
    print("baseline", hashlib.sha256(source_bytes).hexdigest(), len(base["requirements"]))
    print("verified", len(verified_ids), "added; recall", len(recall_ids), "added")


if __name__ == "__main__":
    main()
