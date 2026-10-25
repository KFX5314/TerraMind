"""Offline audit of every 450→360 removal and a conservative intermediate JSON."""

from __future__ import annotations

import hashlib
import json
import unicodedata
from collections import Counter
from pathlib import Path

import pymupdf


ROOT = Path(__file__).resolve().parents[1]
EVAL = ROOT / "artifacts/evaluations"
OUT = EVAL / "heldout-f2-independent-20261025"
BASE = EVAL / "heldout-f2-offline-alternatives-20261025/eval-balanced-source-faithful.json"
CORE = EVAL / "heldout-f2-module-scope-20261025/module-lamp-scope.json"
AGGRESSIVE = EVAL / "heldout-f2-module-scope-20261025/module-evidence-side-recovery-360.json"
RECOVERY = EVAL / "heldout-f2-offline-alternatives-20261025/eval-high-recall.json"
RAW = Path("C:/Users/saish/Certivity/TeraMind/TerraMind/artifacts/runs/heldout-v1/requirements.json")
PKG = Path("C:/Users/saish/Certivity/industrial-ai-hackathon")
EXPECTED_HASHES = {
    BASE: "9c4cbac94ffe34f6ac031744f277d1aade0ce46153f648b2a4d4175725b6b936",
    CORE: "b37685bb18c4f29b8d24eeb14ca8640c184a3b31a695b1c390b39161465d7a24",
    AGGRESSIVE: "02500e7caaab14aa63bd7ee3a0e509f557a781b4f6aeb34c98005af6b4931a5b",
}
PROCEDURE_IDS = {"R-0780", "R-0782", "R-0783", "R-0787", "R-0789", "R-1121", "R-1129"}
REFLECTOR_IDS = {"R-0637", "R-0639", "R-0641", "R-0642", "R-0643", "R-0644", "R-0645",
                 "R-0649", "R-0652", "R-0653", "R-0655", "R-0656", "R-0657"}
ADDED_IDS = {"R-0940", "R-1152"}


def norm(value: str) -> str:
    return " ".join(unicodedata.normalize("NFKC", value).casefold().split())


def scope(item: dict) -> tuple[str, str, str, str, str, str]:
    """Return (component, spec status, drawing, source duty, grade, explanation)."""
    ident = item["id"]
    reg = item["source"]["regulation"]
    para = item["source"]["paragraph"]
    if ident == "R-0361":
        return ("liquid-fuel filler cap", "contradicted: EV charge flap", "EV 'fuel filler cap' label, not a liquid-fuel tank", "mandatory if a fuel-tank filler exists", "A", "An EV charge-port cover is not the fuel-tank filler named by R26 6.6.1.")
    if ident in REFLECTOR_IDS:
        function = "front retro-reflector" if para.startswith("6.16") else "side retro-reflector"
        source_duty = ("optional for most motor vehicles; mandatory if all forward lamps have concealable reflectors" if para.startswith("6.16") else
                       "optional for motor vehicles ≤6 m; mandatory above 6 m")
        return (function, "unspecified, no reflector part listed", "no front or side retro-reflector labelled or discernible", source_duty, "B", "The source applies if the reflector is fitted or a vehicle exception applies; package does not establish either, but absence in a drawing is not proof.")
    if ident == "R-0877":
        return ("active ride-height suspension", "unspecified", "no ride-height system shown", "conditional on ARHSS changing front-axle height", "B", "A vehicle-level suspension option is not identified, although the bumper drawing cannot disprove it.")
    if ident in PROCEDURE_IDS:
        return ("production inspection or sampling", "not described in product spec", "no evidence about production inspection", "mandatory/conditional in conformity-of-production process", "C", "Source states a separate inspection or sampling step. It may be counted as an independently testable obligation, despite overlap with design constraints.")
    if ident in {"R-0891", "R-0892", "R-1194"}:
        return ("active pedestrian-protection device", "sensor shown; deployable device unspecified", "pedestrian sensors labelled; no deployable device labelled", "conditional on a device intended to protect pedestrians", "C", "The shown sensors could trigger a separate active device; absence of that device from the module drawing does not disprove vehicle-level applicability.")
    if ident in {"R-0572", "R-1115"}:
        return ("front/other direction-indicator category", "side signalling listed; exact category unspecified", "signalling strip visible at front corner", "mandatory if a listed front/other category is used", "C", "The strip might serve a front indicator as well as side signalling; do not infer category 5/6 only.")
    if para.startswith("6.9") or para.startswith("5.1") or ident in {"R-0467", "R-0938", "R-1033", "R-1034", "R-1035", "R-1038", "R-1106"}:
        return ("front-position lamp", "generic functional lighting; specific function unspecified", "front-corner signalling strip, function unresolved", "vehicle-level mandatory presence; device limits apply if bumper carries this lamp", "C", "A front-position function could share the depicted lamp; its omission from the parts list does not establish non-applicability.")
    if para.startswith("6.19") or para.startswith("5.4") or para.startswith("Annex 6") or ident in {"R-0472", "R-1107"}:
        return ("daytime-running lamp", "generic functional lighting; specific function unspecified", "front-corner signalling strip, function unresolved", "vehicle-level mandatory presence; device/annex limits apply if bumper carries this lamp", "C", "A DRL could share the depicted strip or another integrated lamp; unknown module allocation is a recall risk.")
    if para.startswith("6.5") or (reg == "UN R148" and (para.startswith("5.6") or para in {"Annex 2", "3.3.2.5.1.1"})):
        return ("front direction-indicator variant", "side signalling listed; exact function/category unspecified", "signalling strip visible at front corner", "mandatory when corresponding front/handed/sequential indicator variant is used", "C", "A front-corner side signalling strip could also serve a front-indicator function; category and sequential operation are unknown.")
    if ident == "R-1115":
        raise AssertionError("handled above")
    raise AssertionError(f"Unclassified removed requirement {ident} {reg} {para}")


def main() -> None:
    for path, digest in EXPECTED_HASHES.items():
        assert hashlib.sha256(path.read_bytes()).hexdigest() == digest
    base_doc = json.loads(BASE.read_text(encoding="utf8"))
    core_doc = json.loads(CORE.read_text(encoding="utf8"))
    aggressive_doc = json.loads(AGGRESSIVE.read_text(encoding="utf8"))
    base = {x["id"]: x for x in base_doc["requirements"]}
    core = {x["id"]: x for x in core_doc["requirements"]}
    aggressive = {x["id"]: x for x in aggressive_doc["requirements"]}
    raw = {x["id"]: x for x in json.loads(RAW.read_text(encoding="utf8"))}
    assert len(base) == 450 and len(core) == 394 and len(aggressive) == 360
    assert len(set(base) - set(aggressive)) == 92 and set(aggressive) - set(base) == ADDED_IDS
    index = {x["regulation"]: next(v["version_label"] for v in x["versions"] if v["role"] == "base")
             for x in json.loads((PKG / "regulations/index.json").read_text(encoding="utf8"))}
    docs = {}
    records = []
    for ident in sorted(set(base) - set(aggressive)):
        item = base[ident]
        src = item["source"]
        assert index[src["regulation"]] == src["version"]
        slug = src["regulation"].replace(" ", "_")
        pdf = PKG / "regulations/pdf" / slug / "base" / f"{slug}_base.pdf"
        docs.setdefault(slug, pymupdf.open(pdf))
        assert 1 <= src["page"] <= len(docs[slug])
        quote = raw[ident]["quote"]
        page = norm(docs[slug][src["page"] - 1].get_text())
        exact = norm(quote) in page
        component, spec_status, drawing, duty, grade, reason = scope(item)
        records.append({
            "id": ident, "classification": grade, "component_or_function": component,
            "spec_status": spec_status, "drawing_evidence": drawing,
            "regulatory_obligation": duty, "could_certivity_consider_applicable": grade in {"B", "C", "D"},
            "reason": reason, "text": item["text"], "source": src,
            "source_pdf": str(pdf), "source_quote": quote,
            "source_support": ("PDF quote exact on cited page" if exact else
                               "Obligation on adjacent PDF page; cited page has section heading" if ident == "R-0637" else
                               "PDF paragraph/table supported after layout or page-split review; quote not contiguous"),
            "saved_applicability": raw[ident]["applicability"],
            "saved_condition": raw[ident].get("condition", ""),
            "present_in_394": ident in core,
        })
    counts = Counter(x["classification"] for x in records)
    assert counts == {"A": 1, "B": 14, "C": 77}
    assert sum(x["source_support"].startswith("PDF quote exact") for x in records) == 76

    additions = []
    saved_recovery = {x["id"]: x for x in json.loads(RECOVERY.read_text(encoding="utf8"))["requirements"]}
    for ident in sorted(ADDED_IDS):
        item = aggressive[ident]
        assert item == saved_recovery[ident]
        src = item["source"]
        assert src["regulation"] == "UN R148" and src["version"] == index["UN R148"]
        page = norm(docs["UN_R148"][src["page"] - 1].get_text())
        assert norm(raw[ident]["quote"]) in page
        additions.append({"id": ident, "text": item["text"], "source": src,
                          "saved_condition": raw[ident].get("condition", ""),
                          "source_quote": raw[ident]["quote"], "source_quote_on_cited_page": True,
                          "product_category_confirmed": False,
                          "risk": "Source duty is valid; actual lamp category/function is unspecified."})

    # The moderate alternative excludes only the EV liquid-fuel misapplication and
    # the 13 unspecified reflectors; it restores every other removed duty.
    remove_intermediate = REFLECTOR_IDS | {"R-0361"}
    intermediate_items = [x for x in base_doc["requirements"] if x["id"] not in remove_intermediate]
    intermediate_items.extend(saved_recovery[i] for i in sorted(ADDED_IDS))
    assert len(intermediate_items) == 438 and len({x["id"] for x in intermediate_items}) == 438
    intermediate = {"team_id": base_doc["team_id"], "case_id": base_doc["case_id"], "requirements": intermediate_items}
    OUT.mkdir(parents=True, exist_ok=False)
    data = (json.dumps(intermediate, ensure_ascii=False, indent=2) + "\n").encode("utf8")
    target = OUT / "verified-intermediate-438.json"
    with target.open("xb") as handle:
        handle.write(data)
    target.chmod(0o444)
    (OUT / "removal-audit.json").write_text(json.dumps({
        "baseline_sha256": EXPECTED_HASHES[BASE], "aggressive_sha256": EXPECTED_HASHES[AGGRESSIVE],
        "classification_counts": dict(counts), "removed": records, "added": additions,
        "intermediate_filename": target.name, "intermediate_sha256": hashlib.sha256(data).hexdigest(),
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf8")
    print("classifications", dict(counts), "source exact", 76, "other source context", 16)
    print("intermediate", len(intermediate_items), hashlib.sha256(data).hexdigest())


if __name__ == "__main__":
    main()
