"""Immutable offline candidates based on the scored 450, retaining all reflectors."""

from __future__ import annotations

import hashlib
import json
import unicodedata
from collections import Counter
from pathlib import Path

import pymupdf


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts/evaluations/heldout-f2-post438-20261025"
BASE = ROOT / "artifacts/evaluations/heldout-f2-offline-alternatives-20261025/eval-balanced-source-faithful.json"
RAW = Path("C:/Users/saish/Certivity/TeraMind/TerraMind/artifacts/runs/heldout-v1/requirements.json")
PKG = Path("C:/Users/saish/Certivity/industrial-ai-hackathon")
BASE_HASH = "9c4cbac94ffe34f6ac031744f277d1aade0ce46153f648b2a4d4175725b6b936"


def norm(value: str) -> str:
    return " ".join(unicodedata.normalize("NFKC", value).casefold().split())


def main() -> None:
    assert hashlib.sha256(BASE.read_bytes()).hexdigest() == BASE_HASH
    baseline = json.loads(BASE.read_text(encoding="utf8"))
    saved = {x["id"]: x for x in json.loads(RAW.read_text(encoding="utf8"))}
    assert len(baseline["requirements"]) == 450
    by_id = {x["id"]: x for x in baseline["requirements"]}
    assert all(i in by_id for i in ("R-0361", "R-0637", "R-1059", "R-1060"))
    changes = {}
    repaired = []
    for original in baseline["requirements"]:
        ident = original["id"]
        if ident == "R-0361":
            changes[ident] = {"action": "remove", "before": original,
                              "reason": "R26 §6.6.1 concerns a liquid-fuel tank filler; the specified EV charging flap is a different component."}
            continue
        item = json.loads(json.dumps(original))
        if ident == "R-0637":
            assert item["source"]["page"] == 56
            item["source"]["page"] = 57
            changes[ident] = {"action": "citation correction", "before": original,
                              "after": item, "reason": "R48 §6.16.2 starts on PDF p.56, but its number/type-approved sentence appears on p.57."}
        elif ident == "R-1059":
            before = item["text"]
            item["text"] = (before.replace("6∙10-1", "0.6").replace("2.80∙102", "280")
                            .replace("1.40∙102", "140"))
            assert item["text"] != before
            changes[ident] = {"action": "numeric notation", "before": original, "after": item,
                              "reason": "Normalize R148 Table 8 category-5 values 6×10^-1, 2.80×10^2, 1.40×10^2 to 0.6, 280, 140 cd."}
        elif ident == "R-1060":
            before = item["text"]
            item["text"] = (before.replace("5.0∙101", "50").replace("2.80∙102", "280")
                            .replace("1.40∙102", "140"))
            assert item["text"] != before
            changes[ident] = {"action": "numeric notation", "before": original, "after": item,
                              "reason": "Normalize R148 Table 8 category-6 values 5.0×10^1, 2.80×10^2, 1.40×10^2 to 50, 280, 140 cd."}
        repaired.append(item)
    assert len(repaired) == 449

    recovery = {
        "R-0362": "If the bumper grille or air guide has movable intake or outlet flaps, the flaps shall meet R26 paragraphs 5.2, 5.3 and 5.4 in every position of use.",
        "R-0940": "If the side signalling lamp is a category 6 direction indicator, the lamp shall show an 'R' or 'L' marking identifying the vehicle side.",
        "R-1152": "If the side signalling lamp is a category 5 or 6 direction indicator, its luminous intensity distribution shall additionally be checked 0.2 seconds after switch-on at reference coordinate H5, V0, as specified in R148 Annex 8 Table A8-1.",
    }
    index = {x["regulation"]: next(v["version_label"] for v in x["versions"] if v["role"] == "base")
             for x in json.loads((PKG / "regulations/index.json").read_text(encoding="utf8"))}
    additions = []
    docs = {}
    for ident, text in recovery.items():
        src = saved[ident]
        assert src["version"] == index[src["regulation"]]
        slug = src["regulation"].replace(" ", "_")
        pdf = PKG / "regulations/pdf" / slug / "base" / f"{slug}_base.pdf"
        docs.setdefault(slug, pymupdf.open(pdf))
        assert norm(src["quote"]) in norm(docs[slug][src["page"] - 1].get_text())
        item = {"id": ident, "text": text,
                "source": {key: src[key] for key in ("regulation", "version", "page", "paragraph")},
                "test_case": src["test_case"]}
        additions.append(item)
        changes[ident] = {"action": "add", "after": item, "source_pdf": str(pdf),
                          "source_quote": src["quote"], "saved_probability": src["probability"],
                          "saved_condition": src.get("condition", ""),
                          "reason": "Saved, source-supported conditional obligation tied to the specified grille/airflow or side signalling function; exact configuration remains unknown."}

    OUT.mkdir(parents=True, exist_ok=False)
    files = {}
    for filename, items in (("source-corrected-449.json", repaired),
                            ("targeted-recovery-452.json", repaired + additions)):
        doc = {"team_id": baseline["team_id"], "case_id": baseline["case_id"], "requirements": items}
        assert len({x["id"] for x in items}) == len(items)
        data = (json.dumps(doc, ensure_ascii=False, indent=2) + "\n").encode("utf8")
        path = OUT / filename
        with path.open("xb") as handle:
            handle.write(data)
        path.chmod(0o444)
        files[filename] = {"count": len(items), "sha256": hashlib.sha256(data).hexdigest(),
                           "by_regulation": dict(Counter(x["source"]["regulation"] for x in items))}
        print(filename, files[filename])
    (OUT / "change-ledger.json").write_text(json.dumps({
        "scored_baseline": str(BASE), "baseline_sha256": BASE_HASH,
        "files": files, "changes": changes,
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf8")


if __name__ == "__main__":
    main()
