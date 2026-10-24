"""Parser check: are the gold (regulation, paragraph) citations found by our parser, on the gold page?

Evaluation only (reads expected.json)."""

from __future__ import annotations

import json
import re
import sys

from . import ingest, paths


def para_key(paragraph) -> str | None:
    """Same normalisation as tools/score_local.py::_paragraph_key."""
    text = str(paragraph or "").casefold().replace("§", " ")
    text = re.sub(r"[,;:()\[\]]", " ", text)
    text = re.sub(r"(?<![0-9a-z])\.|\.(?![0-9a-z])", " ", text)
    text = " ".join(text.split())
    text = re.sub(r"^(paragraphs?|para|par|section|clause)\s+", "", text)
    return text or None


def main(case_id: str = "dev-rear-lamp") -> None:
    gold = json.loads(paths.expected_path(case_id).read_text(encoding="utf-8"))["requirements"]
    found_label = found_page = 0
    misses = []
    docs: dict[str, dict] = {}
    for r in gold:
        s = r["source"]
        if s["regulation"] not in docs:
            docs[s["regulation"]] = ingest.load(s["regulation"], "base")
        doc = docs[s["regulation"]]
        key = para_key(s.get("paragraph"))
        hits = [p for p in doc["paragraphs"] if para_key(p["label"]) == key]
        if hits:
            found_label += 1
            if any(s["page"] in p["pages"] for p in hits):
                found_page += 1
            else:
                misses.append((s["regulation"], s.get("paragraph"), s["page"], "page", [p["pages"] for p in hits]))
        else:
            misses.append((s["regulation"], s.get("paragraph"), s["page"], "label", None))
    n = len(gold)
    print(f"label found: {found_label}/{n} = {found_label / n:.1%}   label+page: {found_page}/{n} = {found_page / n:.1%}")
    for m in sorted(set((a, b, c, d, json.dumps(e)) for a, b, c, d, e in misses)):
        print("  MISS", m)


if __name__ == "__main__":
    main(*(sys.argv[1:2] or []))
