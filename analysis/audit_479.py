"""Deterministic per-requirement source and scope audit of the scored 479 JSON."""

from __future__ import annotations

import json
import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

import pymupdf


ROOT = Path(__file__).resolve().parents[1]
RUN = Path("C:/Users/saish/Certivity/TeraMind/TerraMind/artifacts/runs/heldout-v1")
PKG = Path("C:/Users/saish/Certivity/industrial-ai-hackathon")
EVAL = ROOT / "artifacts/evaluations/heldout-f2-20261025"
OUT = ROOT / "artifacts/evaluations/heldout-f2-audit-20261025"


def norm(value: str) -> str:
    value = unicodedata.normalize("NFKC", value).casefold().replace("−", "-").replace("±", "+/-")
    return " ".join(value.split())


def numerical_tokens(value: str) -> list[str]:
    return re.findall(r"(?<![\w])(?:[+\-]?\d+(?:[.,]\d+)?)(?:\s*(?:mm|nm|km/h|m/s|hz|khz|mhz|v|db|cd|g|%|°))?", norm(value))


def main() -> None:
    submission = json.loads((EVAL / "verified-recovery.json").read_text(encoding="utf8"))
    assert len(submission["requirements"]) == 479
    raw = {x["id"]: x for x in json.loads((RUN / "requirements.json").read_text(encoding="utf8"))}
    ledger = {x["id"]: x for x in json.loads((EVAL / "change-ledger.json").read_text(encoding="utf8"))["added"]}
    docs = {}
    rows = []
    by_signature = defaultdict(list)
    for item in submission["requirements"]:
        ident = item["id"]
        src = item["source"]
        reg = src["regulation"]
        slug = reg.replace(" ", "_")
        pdf = PKG / "regulations/pdf" / slug / "base" / f"{slug}_base.pdf"
        if reg not in docs:
            docs[reg] = pymupdf.open(pdf)
        doc = docs[reg]
        page = src["page"]
        old = raw.get(ident)
        added = ledger.get(ident)
        quote = old["quote"] if old else (added or {}).get("quote", "")
        model_condition = old.get("condition", "") if old else (added or {}).get("model_condition", "")
        applicability = old.get("applicability", "source-reviewed") if old else "source-reviewed"
        page_ok = 1 <= page <= len(doc)
        page_text = doc[page - 1].get_text() if page_ok else ""
        quote_full = bool(quote) and norm(quote) in norm(page_text)
        quote_prefix = bool(quote) and norm(quote)[:50] in norm(page_text)
        adjacent = bool(quote) and any(norm(quote)[:50] in norm(doc[p - 1].get_text())
                                       for p in (page - 1, page + 1) if 1 <= p <= len(doc))
        number_issues = sorted(set(numerical_tokens(item["text"])) - set(numerical_tokens(quote))) if quote else []
        # Content words can differ because the model made a stand-alone sentence. Flag for human review.
        flags = []
        if not page_ok:
            flags.append("invalid_pdf_page")
        elif quote and not (quote_full or quote_prefix or adjacent):
            flags.append("quote_not_contiguous_near_citation")
        elif adjacent and not quote_prefix:
            flags.append("quote_prefix_on_adjacent_page")
        if quote and re.search(r"\bshould\b", quote, re.I) and re.search(r"\bshall\b", item["text"], re.I):
            flags.append("should_to_shall_review")
        if number_issues:
            flags.append("numbers_added_vs_saved_quote_review")
        if applicability == "conditional" and model_condition:
            flags.append("saved_condition_not_exported_as_field")
        para = src.get("paragraph", "")
        if reg == "UN R48" and any(para == p or para.startswith(p + ".") for p in
                                     ("6.3", "6.16", "6.17", "6.20", "6.26", "6.27")):
            flags.append("unconfirmed_r48_function")
        if reg == "UN R148" and para.startswith("3.3"):
            flags.append("mandatory_or_conditional_marking_review")
        row = {
            "id": ident, "text": item["text"], "source": src, "source_pdf": str(pdf),
            "source_quote": quote, "quote_exact_on_page": quote_full,
            "quote_prefix_on_page": quote_prefix, "quote_prefix_adjacent": adjacent,
            "saved_probability": old.get("probability") if old else (added or {}).get("probability"),
            "saved_applicability": applicability, "saved_condition": model_condition,
            "numbers_added_vs_quote": number_issues, "flags": flags,
        }
        rows.append(row)
        by_signature[(reg, norm(item["text"]))].append(ident)
    assert len(rows) == len(submission["requirements"])
    exact_duplicates = [ids for ids in by_signature.values() if len(ids) > 1]
    summary = {
        "count": len(rows), "by_regulation": dict(Counter(x["source"]["regulation"] for x in rows)),
        "flags": dict(Counter(flag for row in rows for flag in row["flags"])),
        "exact_same_regulation_text_duplicates": exact_duplicates,
        "quote_exact_on_cited_page": sum(x["quote_exact_on_page"] for x in rows),
        "quote_prefix_on_cited_page": sum(x["quote_prefix_on_page"] for x in rows),
    }
    OUT.mkdir(parents=True, exist_ok=False)
    (OUT / "requirement-audit.json").write_text(json.dumps({"summary": summary, "requirements": rows}, ensure_ascii=False, indent=2) + "\n", encoding="utf8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
