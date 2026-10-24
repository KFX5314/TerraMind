"""Deterministic PDF -> paragraph tree for the Certivity-rendered regulation PDFs.

Layout facts (verified on R10/R48/R150):
  * page header "UN Rxx, version v | page N of M" in Helvetica 8 -> skipped; cited page = physical page
  * top-level sections ("5. General requirements") and annex headings ("Annex 4 Photometric ...") in Helvetica-Bold 13
  * part headings inside annexes ("Part 1 - ...") in Times-Bold 10.5
  * body text Times 10.5, tables Times 9.5, paragraph labels "5.1.2." at the left margin

Paragraph labels follow the gold format: "6.9.1", "Annex 9 3.1", "Annex 4 Part 1 1.2".
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from collections import Counter
from pathlib import Path

import pymupdf

from . import paths

PARSER_VERSION = "p8"

LABEL_RE = re.compile(r"^(\d{1,2}(?:\.\d{1,3})*)\.(?=\s|$)\s*(.*)$")
HEAD_NODOT_RE = re.compile(r"^(\d{1,2})\s+([A-Z].*)$")  # bold "1 Scope"
LABEL_NODOT_RE = re.compile(r"^(\d{1,2}(?:\.\d{1,3})+)\s+([A-Z(].*)$")  # "5.7 Grouped ..." (typo in source)
ANNEX_RE = re.compile(r"^Annex\s+(\d+[A-Z]?)\b(?:\s*[-–]\s*Appendix\s+(\d+[A-Z]?)\b)?\s*(.*)$")
APPENDIX_RE = re.compile(r"^Appendix\s+(\d+[A-Z]?)\b\s*(.*)$")
PART_RE = re.compile(r"^Part\s+(\d+[A-Z]?)\b\s*[-–:]?\s*(.*)$")


def _lines(page: pymupdf.Page):
    for block in page.get_text("dict")["blocks"]:
        for line in block.get("lines", []):
            spans = [s for s in line["spans"] if s["text"].strip()]
            if not spans:
                continue
            text = "".join(s["text"] for s in line["spans"]).strip()
            s0 = spans[0]
            yield text, s0["font"], round(s0["size"], 1), tuple(round(v, 1) for v in line["bbox"])


def _plausible(cand: tuple[int, ...], last: tuple[int, ...] | None) -> bool:
    if last is None:
        return len(cand) <= 2
    # child: 5.1 -> 5.1.1
    if len(cand) == len(last) + 1 and cand[:-1] == last and cand[-1] <= 3:
        return True
    # sibling or ascending at some depth: 5.1.2 -> 5.1.3 / 5.2 / 6
    d = len(cand)
    if d <= len(last) and cand[: d - 1] == last[: d - 1] and 0 < cand[d - 1] - last[d - 1] <= 6:
        return True
    return False


def parse_pdf(pdf: Path, regulation: str = "", role: str = "", version_label: str = "") -> dict:
    doc = pymupdf.open(pdf)
    paras: list[dict] = []
    scope_annex: str | None = None
    scope_part: str | None = None
    scope_appendix: str | None = None
    last_num: dict[str, tuple[int, ...] | None] = {}
    cur: dict | None = None
    prev_kind = None
    bold_sections = False

    def scope() -> str:
        bits = []
        if scope_annex:
            bits.append(f"Annex {scope_annex}")
        if scope_appendix:
            bits.append(f"Appendix {scope_appendix}")
        if scope_part:
            bits.append(f"Part {scope_part}")
        return " ".join(bits)

    def start(kind: str, num: str, title: str, page_no: int, bbox) -> dict:
        nonlocal cur
        sc = scope()
        label = (f"{sc} {num}".strip() if num else sc) or title[:40]
        cur = {
            "id": len(paras),
            "kind": kind,
            "scope": sc,
            "num": num,
            "label": label,
            "title": title[:160],
            "text": title,
            "page": page_no,
            "pages": [page_no],
            "rects": [[page_no, *bbox]],
        }
        paras.append(cur)
        return cur

    def add(text: str, page_no: int, bbox) -> None:
        if cur is None:
            start("heading", "", "Preamble", page_no, bbox)
        if cur["text"].endswith("-"):
            cur["text"] += text
        else:
            cur["text"] = f"{cur['text']} {text}".strip()
        if page_no not in cur["pages"]:
            cur["pages"].append(page_no)
        cur["rects"].append([page_no, *bbox])

    # sizes are scaled per document: derive thresholds from the modal body / heading sizes
    all_lines = [(pno + 1, ln) for pno in range(doc.page_count) for ln in _lines(doc[pno])]
    times_sizes = Counter(ln[2] for _, ln in all_lines if "Times" in ln[1] and "Bold" not in ln[1])
    hb_sizes = Counter(ln[2] for _, ln in all_lines if "Helvetica" in ln[1] and "Bold" in ln[1])
    body = times_sizes.most_common(1)[0][0] if times_sizes else 10.5
    head = hb_sizes.most_common(1)[0][0] if hb_sizes else body * 1.24
    for page_no, (text, font, size, bbox) in all_lines:
        if True:
            is_helv = "Helvetica" in font
            is_bold = "Bold" in font
            if is_helv and not is_bold:
                continue  # running header / rendering notes
            if is_helv and is_bold and size >= head * 1.15:
                continue  # document title
            if is_helv and is_bold:
                m = ANNEX_RE.match(text)
                if m:
                    scope_annex, scope_appendix, scope_part = m.group(1), m.group(2), None
                    last_num[scope()] = None
                    start("annex", "", m.group(3), page_no, bbox)
                    prev_kind = "heading"
                    continue
                m = APPENDIX_RE.match(text)
                if m and not scope_annex:
                    scope_appendix, scope_part = m.group(1), None
                    last_num[scope()] = None
                    start("appendix", "", m.group(2), page_no, bbox)
                    prev_kind = "heading"
                    continue
                m = LABEL_RE.match(text) or HEAD_NODOT_RE.match(text)
                if m:
                    num = m.group(1)
                    if not scope():
                        bold_sections = True
                    last_num[scope()] = tuple(int(x) for x in num.split("."))
                    start("section", num, m.group(2), page_no, bbox)
                    prev_kind = "heading"
                    continue
                if prev_kind == "heading" and cur is not None:
                    cur["title"] = f"{cur['title']} {text}".strip()[:160]
                    add(text, page_no, bbox)
                    continue
                # unnumbered bold heading ("Introduction (for information)"): own block, keeps its text
                start("heading", "", text, page_no, bbox)
                prev_kind = "heading"
                continue
            if "Times" in font and is_bold and size >= body * 0.95 and scope_annex:
                m = PART_RE.match(text)
                if m:
                    scope_part = m.group(1)
                    last_num[scope()] = None
                    start("part", "", m.group(2), page_no, bbox)
                    prev_kind = "heading"
                    continue
            prev_kind = "body"
            m = LABEL_RE.match(text) or LABEL_NODOT_RE.match(text)
            if m and size >= body * 0.95 and bbox[0] < 80 and "Ital" not in font:
                num = m.group(1)
                cand = tuple(int(x) for x in num.split("."))
                sc = scope()
                if len(cand) == 1 and not sc and bold_sections:
                    add(text, page_no, bbox)  # top-level main-body sections are bold headings in these PDFs
                    continue
                if _plausible(cand, last_num.get(sc)):
                    last_num[sc] = cand
                    start("para", num, m.group(2), page_no, bbox)
                    continue
            add(text, page_no, bbox)

    # parent links: nearest previous paragraph in the same scope whose num is a prefix
    by_scope: dict[str, list[dict]] = {}
    for p in paras:
        p["parent"] = None
        if p["num"]:
            stack = by_scope.setdefault(p["scope"], [])
            while stack and not p["num"].startswith(stack[-1]["num"] + "."):
                stack.pop()
            p["parent"] = stack[-1]["id"] if stack else None
            stack.append(p)
        else:
            by_scope[p["scope"]] = []

    return {
        "parser_version": PARSER_VERSION,
        "regulation": regulation,
        "role": role,
        "version_label": version_label,
        "pdf": str(pdf),
        "sha256": hashlib.sha256(pdf.read_bytes()).hexdigest(),
        "page_count": doc.page_count,
        "paragraphs": paras,
    }


def parsed_path(regulation: str, role: str) -> Path:
    return paths.PARSED / paths.slug(regulation) / f"{role}.json"


def load(regulation: str, role: str = "base", force: bool = False) -> dict:
    out = parsed_path(regulation, role)
    if out.exists() and not force:
        data = json.loads(out.read_text(encoding="utf-8"))
        if data.get("parser_version") == PARSER_VERSION:
            return data
    v = paths.version_entry(regulation, role)
    data = parse_pdf(paths.pdf_path(regulation, role), regulation, role, v["version_label"])
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return data


def load_file(pdf: Path, regulation: str, role: str, version_label: str, force: bool = False) -> dict:
    """Parse an arbitrary PDF (e.g. sub-goal old.pdf/new.pdf), cached next to the corpus."""
    out = paths.PARSED / "_files" / f"{hashlib.sha256(str(pdf.resolve()).encode()).hexdigest()[:16]}.json"
    if out.exists() and not force:
        data = json.loads(out.read_text(encoding="utf-8"))
        if data.get("parser_version") == PARSER_VERSION:
            return data
    data = parse_pdf(pdf, regulation, role, version_label)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return data


def parse_all(force: bool = False) -> None:
    for entry in paths.index():
        for v in entry.get("versions", []):
            try:
                d = load(entry["regulation"], v["role"], force=force)
                n = sum(1 for p in d["paragraphs"] if p["kind"] == "para")
                print(f"{entry['regulation']:<10} {v['role']:<7} {d['page_count']:>4}p {n:>5} paragraphs")
            except Exception as exc:  # keep going; report
                print(f"{entry['regulation']:<10} {v['role']:<7} FAILED {exc}", file=sys.stderr)


if __name__ == "__main__":
    parse_all(force="--force" in sys.argv)
