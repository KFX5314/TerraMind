"""Three immutable held-out submission alternatives from saved artifacts only."""

from __future__ import annotations

import hashlib
import json
import unicodedata
from collections import Counter
from pathlib import Path

import pymupdf


ROOT = Path(__file__).resolve().parents[1]
EVAL = ROOT / "artifacts/evaluations"
OUT = EVAL / "heldout-f2-offline-alternatives-20261025"
SAVED = Path("C:/Users/saish/Certivity/TeraMind/TerraMind/artifacts/runs/heldout-v1")
PKG = Path("C:/Users/saish/Certivity/industrial-ai-hackathon")

ADMIN_REMOVALS = {
    "R-1091": "Conformity-of-production control procedure, rather than a device performance or marking obligation.",
    "R-1092": "Inspector sampling procedure, rather than a device performance or marking obligation.",
    "R-1122": "A retest with another standard light source after a failed random sample; laboratory sampling action.",
    "R-1130": "A retest with another standard light source after a failed random sample; laboratory sampling action.",
}

OPTIONAL_B = {
    "6.3": "Front fog lamp function is absent from the written parts list and exploded drawing.",
    "6.20": "Cornering lamp function is absent from the written parts list and exploded drawing.",
    "6.26": "Manoeuvring lamp function is absent from the written parts list and exploded drawing.",
}

RECOVER_C = {"R-0894", "R-0902", "R-0904", "R-0908", "R-0909", "R-0910", "R-0940", "R-1152"}


def norm(value: str) -> str:
    value = unicodedata.normalize("NFKC", value).casefold().replace("−", "-").replace("±", "+/-")
    return " ".join(value.split())


def save_new(path: Path, data: bytes) -> None:
    with path.open("xb") as handle:
        handle.write(data)


def main() -> None:
    current_bytes = (EVAL / "heldout-f2-20261025/verified-recovery.json").read_bytes()
    assert hashlib.sha256(current_bytes).hexdigest() == "7d97af7fbececfdba7d5e12f878b023eaab66b7c42ccfb132cc05585098232f2"
    current = json.loads(current_bytes)
    a_source = json.loads((EVAL / "heldout-f2-conservative-20261025/focused-recovery-441.json").read_text(encoding="utf8"))
    recall_source = json.loads((EVAL / "heldout-f2-20261025/recall-recovery.json").read_text(encoding="utf8"))
    recall_by_id = {x["id"]: x for x in recall_source["requirements"]}
    raw = {x["id"]: x for x in json.loads((SAVED / "requirements.json").read_text(encoding="utf8"))}
    assert len(current["requirements"]) == 479 and len(a_source["requirements"]) == 441
    original = {x["id"]: x for x in current["requirements"]}
    assert len(original) == 479

    # A inherits the 441-item visual/specification scope review; remove only four
    # further, explicitly procedural CoP sampling/retest items.
    a_requirements = [x for x in a_source["requirements"] if x["id"] not in ADMIN_REMOVALS]
    assert len(a_requirements) == 437

    # B preserves the uncertain reflectors, DRL, answer-back, markings and key EMC
    # test conditions. Exclude only three lighting functions absent from the case.
    b_removed = {}
    b_requirements = []
    for x in current["requirements"]:
        ident = x["id"]
        reg = x["source"]["regulation"]
        para = x["source"].get("paragraph", "")
        group = next((key for key in OPTIONAL_B if reg == "UN R48" and
                      (para == key or para.startswith(key + "."))), None)
        if ident in ADMIN_REMOVALS:
            b_removed[ident] = ADMIN_REMOVALS[ident]
        elif group:
            b_removed[ident] = OPTIONAL_B[group]
        else:
            b_requirements.append(dict(x))
    assert len(b_removed) == 30 and len(b_requirements) == 449
    b_by_id = {x["id"]: x for x in b_requirements}
    # Same words apply in both Annex 7 and Annex 8, but to different tests.
    # State the annex context rather than merging two independently testable steps.
    context = {
        "R-0217": ("During the Annex 7 broadband electromagnetic-emission test, ",
                    "Annex 7 addresses broadband ESA emissions; the original stand-alone sentence omitted that context."),
        "R-0239": ("During the Annex 8 narrowband electromagnetic-emission test, ",
                    "Annex 8 addresses narrowband ESA emissions; the original stand-alone sentence omitted that context."),
    }
    b_modifications = {}
    for ident, (prefix, reason) in context.items():
        previous = b_by_id[ident]["text"]
        b_by_id[ident]["text"] = prefix + previous[0].lower() + previous[1:]
        b_modifications[ident] = {"before": previous, "after": b_by_id[ident]["text"], "reason": reason}
    previous_page = b_by_id["R-0029"]["source"]["page"]
    assert previous_page == 10
    b_by_id["R-0029"]["source"] = dict(b_by_id["R-0029"]["source"], page=11)
    b_modifications["R-0029"] = {"before_page": 10, "after_page": 11,
                                   "reason": "The cited ESA emissions-method sentence continues on PDF page 11; page 10 contains the paragraph heading."}
    # New distinct lower-legform test tolerance, explicitly in the saved R127 source.
    impact = raw["R-0894"]
    assert not impact["exported"] and impact["page"] == 33
    impact_item = {"id": impact["id"], "text": impact["text"],
                   "source": {key: impact[key] for key in ("regulation", "version", "page", "paragraph")},
                   "test_case": impact["test_case"]}
    assert impact_item["id"] not in b_by_id
    b_requirements.append(impact_item)
    assert len(b_requirements) == 450

    # C recovers only selected exact-source obligations from the saved candidate
    # extraction, with R127 lower/upper-legform conditions and conditional R148
    # side-indicator duties. No new model output is generated.
    c_requirements = [dict(x) for x in current["requirements"]]
    c_added = []
    for ident in sorted(RECOVER_C):
        assert ident not in original
        item = impact_item if ident == "R-0894" else recall_by_id[ident]
        c_requirements.append(item)
        c_added.append(item)
    assert len(c_requirements) == 487

    docs = {}
    def source_evidence(item: dict, reason: str) -> dict:
        ident = item["id"]
        old = raw[ident]
        src = item["source"]
        slug = src["regulation"].replace(" ", "_")
        pdf = PKG / "regulations/pdf" / slug / "base" / f"{slug}_base.pdf"
        if slug not in docs:
            docs[slug] = pymupdf.open(pdf)
        pdf_text = docs[slug][src["page"] - 1].get_text()
        quote = old["quote"]
        return {"id": ident, "text": item["text"], "source": src,
                "source_pdf": str(pdf), "source_quote": quote,
                "exact_quote_on_cited_page": norm(quote) in norm(pdf_text),
                "saved_probability": old["probability"], "saved_applicability": old["applicability"],
                "saved_condition": old.get("condition", ""), "reason": reason}

    first_ledger = json.loads((EVAL / "heldout-f2-conservative-20261025/change-ledger.json").read_text(encoding="utf8"))
    prior_reasons = {x["id"]: x["reason"] for x in first_ledger["removed"]}
    c_reasons = {
        "R-0894": "R127 lower-legform test horizontal and vertical impact tolerance ±10 mm; absent from the scored file.",
        "R-0902": "R127 lower-legform impactor bottom height 75 ±10 mm; R127 source independently states it.",
        "R-0904": "R127 upper-legform measuring points must be in the defined bumper test area when that test applies.",
        "R-0908": "R127 upper-legform impact axis and ±2° direction tolerance are independently testable.",
        "R-0909": "R127 upper-legform vertical centreline midpoint has a ±10 mm tolerance, unlike GTR9's printed +10 mm wording.",
        "R-0910": "R127 upper-legform lateral centreline has a distinct ±10 mm location tolerance.",
        "R-0940": "If a category 6 side direction indicator is installed, R148 requires an R/L side indication.",
        "R-1152": "If a category 5/6 side direction indicator is installed, R148 Annex 8 specifies the 0.2-second intensity check.",
    }

    def delta(requirements: list[dict], extra_reasons: dict[str, str], modifications: dict | None = None) -> dict:
        new = {x["id"]: x for x in requirements}
        removed = [source_evidence(original[ident], extra_reasons[ident]) for ident in sorted(set(original) - set(new))]
        added = [source_evidence(new[ident], extra_reasons[ident]) for ident in sorted(set(new) - set(original))]
        return {"count": len(requirements), "by_regulation": dict(Counter(x["source"]["regulation"] for x in requirements)),
                "removed": removed, "added": added, "modified": modifications or {}}

    a_reasons = {**prior_reasons, **ADMIN_REMOVALS, "R-0894": "R127 ±10 mm lower-legform impact tolerance is source-supported."}
    # A's one added requirement was already in the 441 file; delta() reports it against scored 479.
    b_reasons = {**b_removed, "R-0894": "R127 ±10 mm lower-legform impact tolerance is source-supported."}
    c_delta_reasons = c_reasons
    out = {
        "eval-scope-conservative": {"requirements": a_requirements, "ledger": delta(a_requirements, a_reasons)},
        "eval-balanced": {"requirements": b_requirements, "ledger": delta(b_requirements, b_reasons, b_modifications)},
        "eval-high-recall": {"requirements": c_requirements, "ledger": delta(c_requirements, c_delta_reasons)},
    }
    for entry in out.values():
        assert all(x["exact_quote_on_cited_page"] for x in entry["ledger"]["added"])
    OUT.mkdir(parents=True, exist_ok=False)
    save_new(OUT / "scored-479-rollback.json", current_bytes)
    ledgers = {}
    for name, entry in out.items():
        doc = {"team_id": current["team_id"], "case_id": current["case_id"], "requirements": entry["requirements"]}
        data = (json.dumps(doc, ensure_ascii=False, indent=2) + "\n").encode("utf8")
        save_new(OUT / f"{name}.json", data)
        ledgers[name] = entry["ledger"]
        ledgers[name]["sha256"] = hashlib.sha256(data).hexdigest()
        print(name, len(entry["requirements"]), ledgers[name]["sha256"],
              "added", len(entry["ledger"]["added"]), "removed", len(entry["ledger"]["removed"]),
              "modified", len(entry["ledger"]["modified"]))
    (OUT / "change-ledger.json").write_text(json.dumps({
        "baseline": "Officially scored 479-requirement upload; F2 59.1%, recall 74.5%, precision 32.4%",
        "baseline_sha256": hashlib.sha256(current_bytes).hexdigest(),
        "candidates": ledgers,
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf8")


if __name__ == "__main__":
    main()
