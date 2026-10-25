"""Deterministic held-out candidate checks without hidden labels or model calls."""

from __future__ import annotations

import hashlib
import json
import math
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

import pymupdf


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts/evaluations/heldout-f2-post438-20261025"
BASE = ROOT / "artifacts/evaluations/heldout-f2-offline-alternatives-20261025/eval-balanced-source-faithful.json"
SCORED438 = ROOT / "artifacts/evaluations/heldout-f2-independent-20261025/verified-intermediate-438.json"
RAW = Path("C:/Users/saish/Certivity/TeraMind/TerraMind/artifacts/runs/heldout-v1/requirements.json")
PKG = Path("C:/Users/saish/Certivity/industrial-ai-hackathon")
FILES = [BASE, SCORED438, OUT / "source-corrected-449.json", OUT / "side-signal-recovery-451.json", OUT / "targeted-recovery-452.json"]


def norm(value: str) -> str:
    return " ".join(unicodedata.normalize("NFKC", value).casefold().split())


def main() -> None:
    raw = {x["id"]: x for x in json.loads(RAW.read_text(encoding="utf8"))}
    previous = json.loads((ROOT / "artifacts/evaluations/heldout-f2-20261025/change-ledger.json").read_text(encoding="utf8"))
    added_old = {x["id"]: x for x in previous["added"]}
    index = {x["regulation"]: next(v["version_label"] for v in x["versions"] if v["role"] == "base")
             for x in json.loads((PKG / "regulations/index.json").read_text(encoding="utf8"))}
    docs = {}
    results = {}
    parsed = {}
    for path in FILES:
        data = path.read_bytes()
        doc = json.loads(data)
        items = doc["requirements"]
        assert doc["team_id"] == "team-10" and doc["case_id"] == "heldout-front-bumper"
        assert len(items) == len({x["id"] for x in items})
        source_check = Counter()
        unsupported = []
        by_text = defaultdict(list)
        for x in items:
            by_text[(x["source"]["regulation"], norm(x["text"]))].append(x["id"])
            source = x["source"]
            assert index[source["regulation"]] == source["version"]
            slug = source["regulation"].replace(" ", "_")
            pdf = PKG / "regulations/pdf" / slug / "base" / f"{slug}_base.pdf"
            docs.setdefault(slug, pymupdf.open(pdf))
            assert 1 <= source["page"] <= len(docs[slug])
            page_text = norm(docs[slug][source["page"] - 1].get_text())
            quote = norm(raw[x["id"]]["quote"] if x["id"] in raw else added_old[x["id"]]["quote"])
            prefix = " ".join(quote.split()[:min(12, len(quote.split()))])
            source_check["quote_exact" if quote in page_text else "quote_prefix" if prefix in page_text else "layout_or_split"] += 1
            if x["id"] in {"R-0362", "R-0940", "R-1152"} and quote not in page_text:
                unsupported.append(x["id"])
        assert not unsupported
        duplicate_text = [ids for ids in by_text.values() if len(ids) > 1]
        parsed[path.name] = {x["id"]: x for x in items}
        results[path.name] = {
            "count": len(items), "sha256": hashlib.sha256(data).hexdigest(),
            "by_regulation": dict(Counter(x["source"]["regulation"] for x in items)),
            "distinct_regulations": len({x["source"]["regulation"] for x in items}),
            "distinct_pages": len({(x["source"]["regulation"], x["source"]["version"], x["source"]["page"]) for x in items}),
            "source_quote_check": dict(source_check), "identical_text_groups": duplicate_text,
        }
    baseline = parsed[BASE.name]
    for name in ("source-corrected-449.json", "side-signal-recovery-451.json", "targeted-recovery-452.json"):
        current = parsed[name]
        results[name]["added_ids"] = sorted(set(current) - set(baseline))
        results[name]["removed_ids"] = sorted(set(baseline) - set(current))
        results[name]["modified_ids"] = sorted(i for i in set(baseline) & set(current) if baseline[i] != current[i])
    assert results["targeted-recovery-452.json"]["added_ids"] == ["R-0362", "R-0940", "R-1152"]
    assert results["side-signal-recovery-451.json"]["added_ids"] == ["R-0940", "R-1152"]
    assert results["targeted-recovery-452.json"]["removed_ids"] == ["R-0361"]
    assert results["side-signal-recovery-451.json"]["removed_ids"] == ["R-0361"]
    assert results["targeted-recovery-452.json"]["modified_ids"] == ["R-0637", "R-1059", "R-1060"]
    assert results["side-signal-recovery-451.json"]["modified_ids"] == ["R-0637", "R-1059", "R-1060"]
    assert results["source-corrected-449.json"]["modified_ids"] == ["R-0637", "R-1059", "R-1060"]

    # R148 Table 8 category-5/6 source mantissas and powers of ten.
    numeric_checks = {
        "R-1059": {"minimum_cd": (6 * 10**-1, 0.6), "maximum_single_cd": (2.80 * 10**2, 280),
                   "maximum_D_cd": (1.40 * 10**2, 140)},
        "R-1060": {"minimum_cd": (5.0 * 10**1, 50), "maximum_single_cd": (2.80 * 10**2, 280),
                   "maximum_D_cd": (1.40 * 10**2, 140)},
    }
    assert all(math.isclose(a, b) for limits in numeric_checks.values() for a, b in limits.values())
    citation = parsed["targeted-recovery-452.json"]["R-0637"]["source"]
    assert citation["page"] == 57 and "Two, type-approved" in docs["UN_R48"][56].get_text()
    assert "Two, type-approved" not in docs["UN_R48"][55].get_text().split("6.16.2. Number")[-1]

    # Infer integer counts from the rounded platform rates; this is arithmetic,
    # not an evaluator of any new requirement-level match.
    baseline_tp, expected_total = 157, 208
    assert round(100 * baseline_tp / 450, 1) == 34.9
    assert round(100 * baseline_tp / expected_total, 1) == 75.5
    assert round(100 * 5 * baseline_tp / (4 * expected_total + 450), 1) == 61.2
    assert round(100 * 155 / 438, 1) == 35.4
    assert round(100 * 155 / expected_total, 1) == 74.5
    assert round(100 * 5 * 155 / (4 * expected_total + 438), 1) == 61.0
    scenarios = {}
    for n in (449, 451, 452):
        scenarios[str(n)] = []
        for removed_match in (0, 1):
            for added_match in range(0, 4 if n == 452 else 3 if n == 451 else 1):
                tp = baseline_tp - removed_match + added_match
                scenarios[str(n)].append({"removed_baseline_matches": removed_match,
                                          "added_matches": added_match,
                                          "hypothetical_f2_percent": round(100 * 5 * tp / (4 * expected_total + n), 3)})

    result = {
        "method": "Official held-out score arithmetic plus deterministic local structure, source-page quote, citation, numeric-equivalence and duplicate checks. No hidden-gold F2 evaluation is possible offline.",
        "official_observations": {"450": {"count": 450, "tp_inferred": 157, "f2": 61.2, "precision": 34.9, "recall": 75.5},
                                  "438": {"count": 438, "tp_inferred": 155, "f2": 61.0, "precision": 35.4, "recall": 74.5},
                                  "expected_total_inferred": expected_total},
        "files": results, "numeric_checks": numeric_checks, "hypothetical_scenarios": scenarios,
    }
    (OUT / "offline-evaluation.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf8")
    for name, item in results.items():
        print(name, item["count"], item["source_quote_check"],
              "duplicates", len(item["identical_text_groups"]))
    print("offline-evaluation.json written; no requirement-level score estimated")


if __name__ == "__main__":
    main()
