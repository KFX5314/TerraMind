"""Structured tables (PyMuPDF find_tables) rendered as markdown and attached to the paragraph they belong to.

The flattened text of a table is unusable for "one requirement per row"; the markdown version lets the model read
row and column headers. Cached per document next to the parsed paragraphs."""

from __future__ import annotations

import json
from pathlib import Path

import pymupdf

from . import paths

TABLES_VERSION = "t2"


def _cell(c) -> str:
    return " ".join((c or "").split())


def _markdown(rows: list[list]) -> str:
    rows = [[_cell(c) for c in r] for r in rows if any(_cell(c) for c in r)]
    if len(rows) < 2:
        return ""
    width = max(len(r) for r in rows)
    rows = [r + [""] * (width - len(r)) for r in rows]
    lines = ["| " + " | ".join(rows[0]) + " |", "|" + "---|" * width]
    lines += ["| " + " | ".join(r) + " |" for r in rows[1:]]
    return "\n".join(lines)


def _cell_text(page, rect) -> str:
    ws = page.get_text("words", clip=pymupdf.Rect(rect))
    ws.sort(key=lambda w: (round(w[1] / 3), w[0]))
    return " ".join(w[4] for w in ws)


def extract_tables(pdf: Path) -> list[dict]:
    doc = pymupdf.open(pdf)
    out = []
    for pno in range(doc.page_count):
        page = doc[pno]
        try:
            found = page.find_tables()
        except Exception:
            continue
        for t in found.tables:
            if t.row_count < 2 or t.col_count < 2:
                continue
            rows = [[_cell_text(page, c) if c else "" for c in row.cells] for row in t.rows]
            md = _markdown(rows)
            if md:
                out.append({"page": pno + 1, "bbox": [round(v, 1) for v in t.bbox], "markdown": md})
    return out


def tables_for(pdf: Path, cache_key: str) -> list[dict]:
    cache = paths.PARSED / "_tables" / f"{cache_key}.json"
    if cache.exists():
        data = json.loads(cache.read_text(encoding="utf-8"))
        if data.get("version") == TABLES_VERSION:
            return data["tables"]
    tables = extract_tables(pdf)
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps({"version": TABLES_VERSION, "tables": tables}, ensure_ascii=False), encoding="utf-8")
    return tables


def attach(paragraphs: list[dict], tables: list[dict]) -> dict[int, str]:
    """Map paragraph id -> markdown of the tables whose bbox falls inside that paragraph's line boxes."""
    out: dict[int, str] = {}
    for t in tables:
        page, (x0, y0, x1, y1) = t["page"], t["bbox"]
        best, best_id = 0.0, None
        for p in paragraphs:
            if page not in p["pages"]:
                continue
            rects = [r for r in p["rects"] if r[0] == page]
            if not rects:
                continue
            top = min(r[2] for r in rects)
            bottom = max(r[4] for r in rects)
            # table starts after the paragraph's first line and before the next paragraph starts
            if top - 2 <= y0 <= bottom + 40:
                score = 1.0 / (1.0 + abs(y0 - bottom))
                if score > best:
                    best, best_id = score, p["id"]
        if best_id is not None:
            out[best_id] = out.get(best_id, "") + "\n\nTABLE (structured):\n" + t["markdown"]
    return out
