"""Main-goal pipeline: product understanding -> regulation screening -> section extraction -> audit -> export.

Every stage writes a JSON artifact into artifacts/runs/<run_id>/; model calls are cached, so re-running a run resumes.
Inference reads only product inputs, the regulation corpus and prompts - never expected.json.
"""

from __future__ import annotations

import asyncio
import datetime as dt
import json
import re
import traceback
from difflib import SequenceMatcher
from pathlib import Path

from . import ingest, llm, paths, prompts, tables

import os

CHUNK_CHARS = int(os.environ.get("CERTI_CHUNK_CHARS", "8000"))
DEFAULT_THRESHOLD = 0.5  # measured on dev (v1 sweep): best F2; the model probability is not calibrated
ALLOWED_INPUT_SUFFIXES = {".md", ".txt", ".png", ".jpg", ".jpeg", ".webp"}


# --------------------------------------------------------------------------------------------- run bookkeeping
class Run:
    def __init__(self, run_id: str):
        self.id = run_id
        self.dir = paths.RUNS / run_id
        self.dir.mkdir(parents=True, exist_ok=True)

    def write(self, name: str, data) -> None:
        (self.dir / name).write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")

    def read(self, name: str):
        f = self.dir / name
        return json.loads(f.read_text(encoding="utf-8")) if f.exists() else None

    def status(self, stage: str, message: str = "", progress: float | None = None, **extra) -> None:
        st = self.read("status.json") or {"events": []}
        st.update({"stage": stage, "message": message, "progress": progress,
                   "updated": dt.datetime.now(dt.timezone.utc).isoformat(), **extra})
        st["events"].append({"t": st["updated"], "stage": stage, "message": message})
        st["events"] = st["events"][-200:]
        st["spent_usd"] = round(llm.spent(), 3)
        self.write("status.json", st)
        print(f"[{self.id}] {stage}: {message}", flush=True)


def new_run_id(case_id: str) -> str:
    return f"{case_id}-{dt.datetime.now().strftime('%Y%m%d-%H%M%S')}"


# --------------------------------------------------------------------------------------------- inputs
def load_case_inputs(case_id: str) -> dict:
    """Product inputs of a case folder. Only spec/drawing files; expected answers are never read."""
    folder = paths.case_dir(case_id)
    spec_parts, images = [], []
    for f in sorted(folder.iterdir()):
        if f.name.lower().startswith("expected") or f.suffix.lower() not in ALLOWED_INPUT_SUFFIXES:
            continue
        if f.suffix.lower() in {".md", ".txt"}:
            spec_parts.append(f"# file: {f.name}\n{f.read_text(encoding='utf-8')}")
        else:
            images.append(str(f))
    return {"case_id": case_id, "spec": "\n\n".join(spec_parts) or None, "images": images}


# --------------------------------------------------------------------------------------------- stage 1
async def understand(inputs: dict, deep_image: bool = False) -> dict:
    content: list[dict] = []
    for img in inputs["images"]:
        content.append(llm.image_block(Path(img)))
    text = []
    if inputs.get("spec"):
        text.append(f"<specification>\n{inputs['spec']}\n</specification>")
    else:
        text.append("No written specification is available: build the profile from the drawing only, marking "
                    "every non-legible fact as inferred or unknown.")
    if inputs["images"]:
        text.append(f"{len(inputs['images'])} drawing(s) attached (exploded view).")
        if deep_image:
            text.append("DEEP IMAGE ANALYSIS: inspect every region of the drawing systematically (callouts, labels, "
                        "small parts, fasteners, connectors, lenses, reflectors, sensors); list each identifiable part.")
    text.append("Build the product profile.")
    content.append({"type": "text", "text": "\n\n".join(text)})
    return await llm.call_json(system=prompts.PROFILE_SYSTEM, content=content, schema=prompts.PROFILE_SCHEMA,
                               tag="profile", model=llm.role_model("profile"),
                               effort=llm.role_effort("profile", "xhigh" if deep_image else "high"), max_tokens=32000)


# --------------------------------------------------------------------------------------------- stage 2
def _clip(text: str, n: int) -> str:
    return text if len(text) <= n else text[:n] + " [...]"


def screening_material(regulation: str) -> str:
    entry = paths.regulation_entry(regulation)
    base = paths.version_entry(regulation, "base")
    doc = ingest.load(regulation, "base")
    ps = doc["paragraphs"]
    intro = " ".join(p["text"] for p in ps if p["kind"] == "heading" and p["title"].lower().startswith("introduction"))
    scope_ps = [p for p in ps if not p["scope"] and re.match(r"(scope|application|purpose)", p["title"], re.I)]
    scope_text = ""
    for sp in scope_ps[:2]:
        group = [sp] + [p for p in ps if p["num"].startswith(sp["num"] + ".") and not p["scope"]
                        and p["id"] > sp["id"] and p["id"] < sp["id"] + 40]
        scope_text += " ".join(f"{p['num']}. {p['text']}" for p in group) + " "
    if not scope_text:  # fall back to the first paragraphs of the main text
        scope_text = " ".join(p["text"] for p in ps if not p["scope"] and p["kind"] != "heading")[:2500]
    cease = [p["text"] for p in ps if re.search(r"cease to grant|shall no longer grant", p["text"], re.I)]
    out = [f"<regulation id=\"{regulation}\">", f"Title: {entry.get('title')}", f"Base version: {base['version_label']}"]
    if intro:
        out.append(f"Introduction: {_clip(intro, 900)}")
    out.append(f"<scope>{_clip(scope_text.strip(), 2500)}</scope>")
    if cease:
        out.append(f"Transitional: {_clip(' | '.join(cease), 600)}")
    out.append("</regulation>")
    return "\n".join(out)


async def _screen_call(profile: dict, regs: list[str], tag: str) -> dict[str, dict]:
    material = "\n\n".join(screening_material(r) for r in regs)
    content = (f"<product_profile>\n{json.dumps(profile, ensure_ascii=False, indent=1)}\n</product_profile>\n\n"
               f"Corpus ({len(regs)} regulations):\n\n{material}\n\n"
               f"Return one decision for each of the {len(regs)} regulations.")
    res = await llm.call_json(system=prompts.SCREEN_SYSTEM, content=content, schema=prompts.screen_schema(regs),
                              tag=tag, model=llm.role_model("screen"), effort=llm.role_effort("screen"),
                              max_tokens=32000)
    return {d["regulation"]: d for d in res["decisions"]}


async def screen(profile: dict) -> list[dict]:
    regs = [e["regulation"] for e in paths.index()]
    got = await _screen_call(profile, regs, "screen")
    missing = [r for r in regs if r not in got]
    if missing:  # the model skipped some regulations: ask again for exactly those, once
        got.update(await _screen_call(profile, missing, "screen:retry"))
    decisions = []
    for r in regs:  # every index entry gets a decision; still-missing ones are explicit and flagged
        d = got.get(r) or {"regulation": r, "decision": "potentially_applicable", "basis": "none", "needs_review": True,
                           "reason": "No decision returned by the screening model after a retry; NOT selected "
                                     "automatically, review manually.", "probability": 0.3}
        d["title"] = paths.regulation_entry(r).get("title")
        d["version"] = paths.version_entry(r, "base")["version_label"]
        decisions.append(d)
    return decisions


def selected_regulations(decisions: list[dict], min_probability: float = 0.5) -> list[str]:
    # the model's probability is the deciding signal: a low-probability "applicable" adds a whole regulation of extras
    return [d["regulation"] for d in decisions
            if d["decision"] != "not_applicable" and d["probability"] >= min_probability]


# --------------------------------------------------------------------------------------------- stage 3
def _top_title(doc: dict, p: dict) -> str:
    """Title of the top-level main-body section a paragraph belongs to."""
    if p["scope"]:
        return p["scope"]
    top = p["num"].split(".")[0]
    for q in doc["paragraphs"]:
        if not q["scope"] and q["num"] == top:
            return q["title"]
    return ""


def chunks_for(regulation: str) -> list[dict]:
    doc = ingest.load(regulation, "base")
    table_md = tables.attach(doc["paragraphs"], tables.tables_for(Path(doc["pdf"]), f"{paths.slug(regulation)}_base"))
    top_titles: dict[str, str] = {}
    chunks: list[dict] = []
    cur: list[dict] = []
    size = 0
    last_group = None

    def flush():
        nonlocal cur, size
        if cur:
            chunks.append({"regulation": regulation, "index": len(chunks), "paragraphs": cur})
        cur, size = [], 0

    # GTRs carry a long "statement of technical rationale" before the regulation text, whose numbering restarts:
    # start at the last main-body section "1" titled purpose/scope/application.
    starts = [q["id"] for q in doc["paragraphs"] if not q["scope"] and q["num"] == "1"
              and re.match(r"(purpose|scope|application)", q["title"], re.I)]
    ones = [q["id"] for q in doc["paragraphs"] if not q["scope"] and q["num"] == "1"]
    first_id = starts[-1] if starts and ones and ones[0] < starts[-1] else 0
    for p in doc["paragraphs"]:
        if p["id"] < first_id:
            continue
        if p["kind"] == "heading" and p["title"].lower().startswith(("introduction", "preamble")):
            continue
        key = p["scope"] or p["num"].split(".")[0]
        if key not in top_titles:
            top_titles[key] = _top_title(doc, p)
        if not p["scope"] and re.match(r"definitions?\b", top_titles[key], re.I):
            continue  # definitions are context, not obligations
        group = p["scope"] or "main"
        text = p["text"] + table_md.get(p["id"], "")
        pieces = [text[i:i + CHUNK_CHARS] for i in range(0, len(text), CHUNK_CHARS)] or [""]
        for piece in pieces:
            item = {"label": p["label"], "pages": p["pages"], "text": piece}
            if cur and (size + len(piece) > CHUNK_CHARS or (group != last_group and size > 3000)):
                flush()
            cur.append(item)
            size += len(piece) + len(p["label"]) + 20
            last_group = group
    flush()
    return chunks


def _format_paragraphs(chunk: dict) -> str:
    lines = []
    for p in chunk["paragraphs"]:
        pg = p["pages"][0] if len(p["pages"]) == 1 else f"{p['pages'][0]}-{p['pages'][-1]}"
        lines.append(f"[{p['label']}] (page {pg}) {p['text']}")
    return "\n".join(lines)


def _reg_header(regulation: str, decision: dict | None) -> str:
    base = paths.version_entry(regulation, "base")
    entry = paths.regulation_entry(regulation)
    why = f"\nWhy it applies: {decision['reason']}" if decision else ""
    return f"Regulation: {regulation} - {entry.get('title')} (version {base['version_label']}){why}"


async def extract_chunk(profile: dict, chunk: dict, decision: dict | None, audit_of: list[dict] | None = None) -> list[dict]:
    labels = sorted({p["label"] for p in chunk["paragraphs"]})
    content = (f"<product_profile>\n{json.dumps(profile, ensure_ascii=False, indent=1)}\n</product_profile>\n\n"
               f"{_reg_header(chunk['regulation'], decision)}\n\n"
               f"<paragraphs>\n{_format_paragraphs(chunk)}\n</paragraphs>\n")
    if audit_of is not None:
        listed = "\n".join(f"- [{r['paragraph']}] {r['text']}" for r in audit_of) or "(none)"
        content += f"\nRequirements already extracted by the first reviewer:\n{listed}\n\nReturn only missing requirements."
        system, tag = prompts.AUDIT_SYSTEM, f"audit:{chunk['regulation']}:{chunk['index']}"
    else:
        content += "\nExtract the requirements that apply to this product."
        system, tag = prompts.EXTRACT_SYSTEM, f"extract:{chunk['regulation']}:{chunk['index']}"
    try:
        role = "audit" if audit_of is not None else "extract"
        res = await llm.call_json(system=system, content=content, schema=prompts.extract_schema(labels), tag=tag,
                                  model=llm.role_model(role), effort=llm.role_effort(role), max_tokens=64000)
    except llm.Truncated:
        if len(chunk["paragraphs"]) < 2:
            raise
        half = len(chunk["paragraphs"]) // 2
        parts = [dict(chunk, paragraphs=chunk["paragraphs"][:half], index=f"{chunk['index']}a"),
                 dict(chunk, paragraphs=chunk["paragraphs"][half:], index=f"{chunk['index']}b")]
        out = []
        for part in parts:
            out += await extract_chunk(profile, part, decision, audit_of)
        return out
    reqs = res["requirements"]
    for r in reqs:
        r["quote"] = r.get("sentence") or r.get("quote", "")
        r["fidelity"] = fidelity(r["quote"], r["text"])
        r.update(evidence_checks(r["quote"], r["text"]))
        r["regulation"] = chunk["regulation"]
        r["chunk"] = chunk["index"]
        r["pass"] = "audit" if audit_of is not None else "extract"
    return reqs


# --------------------------------------------------------------------------------------------- finalisation
def _norm(s: str) -> str:
    # engineering operators must survive normalisation: "<= 10 N" and ">= 10 N", "-10 V" and "10 V" differ
    s = (s.replace("≤", "<=").replace("≥", ">=").replace("±", "+-").replace("−", "-").replace("–", "-")
         .replace("—", "-"))
    return re.sub(r"\s+", " ", re.sub(r"[^0-9a-z%°.,<>=+\- ]", " ", s.casefold())).strip()


NEGATIONS = {"not", "no", "never", "neither", "nor", "cannot", "without"}
NUM_RE = re.compile(r"(?<![\w.])([<>]=?|\+-|[+-])?\s?(\d+(?:[.,]\d+)?)")


def numeric_signature(text: str) -> tuple:
    """Numbers of a text in order, each with its attached sign/comparison operator."""
    return tuple((m.group(1) or "", m.group(2).replace(",", ".")) for m in NUM_RE.finditer(_norm(text)))


def negation_count(text: str) -> int:
    return sum(1 for w in _norm(text).split() if w in NEGATIONS)


def resolve_page_ex(regulation: str, label: str, quote: str) -> tuple[int | None, str]:
    """(page, status). status: 'verified' (the quote was found on that page), 'fallback' (paragraph start page, the
    quote was not found: a navigation hint, not evidence) or 'unresolved' (label not in the parsed document)."""
    doc = ingest.load(regulation, "base")
    hits = [p for p in doc["paragraphs"] if p["label"] == label]
    if not hits:
        return None, "unresolved"
    q = _norm(quote)[:60]
    for p in hits:
        if len(p["pages"]) == 1:
            if q and q[:30] in _norm(p["text"]):
                return p["pages"][0], "verified"
            if not q:
                return p["pages"][0], "fallback"
    # multi-page paragraph (or quote not found in a single-page one): find the page whose lines contain the quote
    import pymupdf
    pdf = pymupdf.open(doc["pdf"])
    for p in hits:
        for pg in p["pages"]:
            if q and q[:30] in _norm(pdf[pg - 1].get_text()):
                return pg, "verified"
    return hits[0]["pages"][0], "fallback"


def resolve_page(regulation: str, label: str, quote: str) -> int | None:
    return resolve_page_ex(regulation, label, quote)[0]


def fidelity(sentence: str, text: str) -> float:
    """Share of the source sentence's content words that survive in the requirement text.

    Word retention only: it is NOT entailment. Polarity and quantities are checked separately (evidence_checks)."""
    stop = {"the", "a", "an", "of", "to", "in", "and", "or", "be", "shall", "is", "are", "for", "with", "by", "on", "at",
            "as", "that", "this", "it", "its", "which", "their", "they", "if"}  # negations are content words
    src = [w for w in _norm(sentence).split() if w not in stop]
    if not src:
        return 1.0
    have = set(_norm(text).split())
    return sum(1 for w in src if w in have) / len(src)


def evidence_checks(sentence: str, text: str) -> dict:
    """Cheap deterministic evidence flags for a requirement against its source sentence. They are review flags, never a
    gate on their own: a sentence with several clauses can legitimately yield requirements with fewer negations."""
    if not sentence:
        return {"polarity_ok": None, "numbers_ok": None}
    src_nums = set(numeric_signature(sentence))
    return {"polarity_ok": negation_count(sentence) == negation_count(text),
            "numbers_ok": all(n in src_nums for n in numeric_signature(text))}


def _same_obligation(a: dict, b: dict) -> bool:
    """Guard in front of the text-similarity merge: two candidates are the same obligation only if they sit in the same
    paragraph, carry the same numbers with the same signs/operators, the same negation and the same condition."""
    return (a["regulation"] == b["regulation"] and a["paragraph"] == b["paragraph"]
            and numeric_signature(a["text"]) == numeric_signature(b["text"])
            and negation_count(a["text"]) == negation_count(b["text"])
            and _norm(a.get("condition", "")) == _norm(b.get("condition", "")))


def dedupe(cands: list[dict]) -> list[dict]:
    """Merge duplicates (highest probability wins). Text similarity discovers candidates; the guard decides.
    Similar-but-distinct candidates are kept and cross-listed under 'similar' for review."""
    kept: list[dict] = []
    for c in sorted(cands, key=lambda c: -c["probability"]):
        n = _norm(c["text"])
        dup = False
        for k in kept:
            if k["regulation"] != c["regulation"]:
                continue
            if SequenceMatcher(None, n, k["_n"]).ratio() <= 0.9:
                continue
            if _same_obligation(c, k):
                dup = True
                k.setdefault("merged", []).append(c["text"])
                break
            k.setdefault("similar", []).append(c["text"])
        if not dup:
            c["_n"] = n
            kept.append(c)
    for k in kept:
        k.pop("_n", None)
    return kept


def finalize(run: Run, candidates: list[dict], team_id: str, case_id: str, threshold: float) -> dict:
    for c in candidates:
        c["version"] = paths.version_entry(c["regulation"], "base")["version_label"]
        c["page"], c["page_status"] = resolve_page_ex(c["regulation"], c["paragraph"], c.get("quote", ""))
    cands = [c for c in candidates if c["page"]]
    uniq = dedupe(cands)
    order = {e["regulation"]: i for i, e in enumerate(paths.index())}
    uniq.sort(key=lambda c: (order.get(c["regulation"], 999), c["page"], c["paragraph"]))
    for i, c in enumerate(uniq, 1):
        c["id"] = f"R-{i:04d}"
        c["exported"] = c["probability"] >= threshold
    run.write("requirements.json", uniq)
    sub = {
        "team_id": team_id,
        "case_id": case_id,
        "requirements": [
            {"id": c["id"], "text": c["text"][:2000],
             "source": {"regulation": c["regulation"], "version": c["version"], "page": c["page"],
                        "paragraph": c["paragraph"]},
             **({"test_case": c["test_case"]} if c.get("test_case") else {})}
            for c in uniq if c["exported"]
        ],
    }
    run.write("submission.json", sub)
    return sub


# --------------------------------------------------------------------------------------------- orchestration
async def run_pipeline(run: Run, inputs: dict, team_id: str, *, deep_image: bool = False, audit: bool = False,
                       threshold: float = DEFAULT_THRESHOLD, only_regulations: list[str] | None = None) -> dict:
    run.write("inputs.json", {**inputs, "config": {"deep_image": deep_image, "audit": audit, "threshold": threshold,
                                                   "model": llm.MODEL, "prompt_version": prompts.PROMPT_VERSION, "chunk_chars": CHUNK_CHARS,
                                                   "parser_version": ingest.PARSER_VERSION}})
    run.status("understanding", "Reading specification and drawing")
    profile = run.read("profile.json") or await understand(inputs, deep_image)
    run.write("profile.json", profile)

    run.status("screening", f"Screening all {len(paths.index())} regulations in the index")
    decisions = run.read("screening.json") or await screen(profile)
    run.write("screening.json", decisions)
    regs = only_regulations or selected_regulations(decisions)
    dec_by = {d["regulation"]: d for d in decisions}
    undecided = [d["regulation"] for d in decisions if d.get("needs_review")]
    if undecided:
        run.status("screening", f"WARNING: no screening decision for {len(undecided)} regulations: {undecided}",
                   undecided=undecided)

    chunks = [c for r in regs for c in chunks_for(r)]
    run.status("extracting", f"Extracting from {len(regs)} regulations in {len(chunks)} sections", 0.0,
               regulations=regs)
    done = 0
    ledger = []

    async def one(chunk):
        nonlocal done
        entry = {"regulation": chunk["regulation"], "chunk": chunk["index"],
                 "labels": [p["label"] for p in chunk["paragraphs"]], "status": "pending"}
        try:
            reqs = await extract_chunk(profile, chunk, dec_by.get(chunk["regulation"]))
            if audit:
                reqs += await extract_chunk(profile, chunk, dec_by.get(chunk["regulation"]), audit_of=reqs)
            entry.update(status="done", n_requirements=len(reqs),
                         n_audit=sum(1 for r in reqs if r["pass"] == "audit"))
        except Exception as exc:  # recorded, never silently dropped
            reqs = []
            entry.update(status="failed", error=f"{type(exc).__name__}: {exc}")
            traceback.print_exc()
        ledger.append(entry)
        done += 1
        run.status("extracting", f"{done}/{len(chunks)} sections processed", done / max(1, len(chunks)))
        return reqs

    results = await asyncio.gather(*(one(c) for c in chunks))
    candidates = [r for rs in results for r in rs]
    run.write("candidates.json", candidates)
    run.write("coverage.json", sorted(ledger, key=lambda e: (e["regulation"], str(e["chunk"]))))

    run.status("finalizing", "Deduplicating, resolving pages, exporting")
    sub = finalize(run, candidates, team_id, inputs["case_id"], threshold)
    failed = sum(1 for e in ledger if e["status"] == "failed")
    run.status("completed" if not failed else "partial",
               f"{len(sub['requirements'])} requirements exported from {len(regs)} regulations"
               + (f"; {failed} sections failed" if failed else ""), 1.0,
               n_requirements=len(sub["requirements"]), failed_sections=failed)
    return sub
