"""FastAPI backend for the engineer UI. Runs the same certi pipeline as the CLI in background threads.

    .venv/Scripts/python -m uvicorn server.app:app --port 8000
"""

from __future__ import annotations

import datetime as dt
import json
import re
import shutil
import subprocess
import sys
import threading
import traceback
import uuid
from functools import lru_cache
from pathlib import Path

import pymupdf
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles

from certi import ingest, llm, paths, pipeline

app = FastAPI(title="Certivity Requirements Agent")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

UPLOADS = paths.DATA / "uploads"
UPLOADS.mkdir(parents=True, exist_ok=True)
SUBGOAL_RUNS = paths.ARTIFACTS / "subgoal"
SUBGOAL_RUNS.mkdir(parents=True, exist_ok=True)
_jobs: dict[str, threading.Thread] = {}


def _team() -> str:
    import os
    return os.environ.get("TEAM_ID", "team-XX")


# ------------------------------------------------------------------------------------------- cases & inputs
@app.get("/api/cases")
def cases():
    out = []
    dirs = list((paths.PKG / "cases").iterdir()) + (list(paths.LOCAL_CASES.iterdir()) if paths.LOCAL_CASES.exists() else [])
    for d in sorted(dirs, key=lambda d: d.name):
        if d.is_dir():
            files = [f.name for f in d.iterdir() if not f.name.lower().startswith("expected")]
            out.append({"case_id": d.name, "files": files, "has_expected": (d / "expected.json").exists()})
    subs = []
    for d in sorted((paths.PKG / "subgoal").iterdir()):
        if d.is_dir() and (d / "requirements_old.json").exists():
            subs.append({"case_id": f"subgoal-{d.name}", "has_pdfs": (d / "old.pdf").exists() and (d / "new.pdf").exists()})
    return {"cases": out, "subgoal_cases": subs}


@app.get("/api/cases/{case_id}/inputs")
def case_inputs(case_id: str):
    inp = pipeline.load_case_inputs(case_id)
    return {"case_id": case_id, "spec": inp["spec"],
            "images": [f"/api/cases/{case_id}/file/{Path(p).name}" for p in inp["images"]]}


@app.get("/api/cases/{case_id}/file/{name}")
def case_file(case_id: str, name: str):
    f = (paths.case_dir(case_id) / name).resolve()
    if not str(f).startswith(str(paths.case_dir(case_id).resolve())) or f.name.lower().startswith("expected"):
        raise HTTPException(404)
    return FileResponse(f)


@app.get("/api/uploads/{upload_id}/{name}")
def upload_file(upload_id: str, name: str):
    f = (UPLOADS / upload_id / name).resolve()
    if not str(f).startswith(str(UPLOADS.resolve())) or not f.exists():
        raise HTTPException(404)
    return FileResponse(f)


# ------------------------------------------------------------------------------------------- runs
def _start_run(run: pipeline.Run, inputs: dict, deep: bool, audit: bool, team_id: str) -> None:
    def work():
        try:
            llm.run(pipeline.run_pipeline(run, inputs, team_id, deep_image=deep, audit=audit))
            _validate_into(run)
        except Exception as exc:
            traceback.print_exc()
            run.status("failed", f"{type(exc).__name__}: {exc}")

    t = threading.Thread(target=work, daemon=True)
    _jobs[run.id] = t
    t.start()


def _validate_into(run: pipeline.Run) -> dict:
    sub = run.dir / "submission.json"
    r = subprocess.run([sys.executable, str(paths.PKG / "tools" / "validate.py"), str(sub)], capture_output=True, text=True)
    rep = {"ok": r.returncode == 0, "output": (r.stdout or r.stderr).strip(),
           "checked": dt.datetime.now(dt.timezone.utc).isoformat()}
    run.write("validation.json", rep)
    return rep


@app.post("/api/runs")
def start_run(body: dict):
    case_id = body["case_id"]
    inputs = pipeline.load_case_inputs(case_id)
    run = pipeline.Run(pipeline.new_run_id(case_id))
    run.status("queued", "Queued")
    _start_run(run, inputs, bool(body.get("deep_image")), body.get("audit", False), body.get("team_id") or _team())
    return {"run_id": run.id}


@app.post("/api/runs/upload")
async def start_upload_run(case_id: str = Form("custom-product"), spec_text: str = Form(""),
                           deep_image: bool = Form(False), audit: bool = Form(False),
                           files: list[UploadFile] = File(default=[])):
    uid = uuid.uuid4().hex[:10]
    folder = UPLOADS / uid
    folder.mkdir(parents=True)
    images = []
    spec_parts = [spec_text] if spec_text.strip() else []
    for f in files:
        name = re.sub(r"[^A-Za-z0-9._-]", "_", f.filename or "file")
        target = folder / name
        target.write_bytes(await f.read())
        if target.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}:
            images.append(str(target))
        elif target.suffix.lower() in {".md", ".txt"}:
            spec_parts.append(target.read_text(encoding="utf-8", errors="replace"))
    inputs = {"case_id": case_id, "spec": "\n\n".join(spec_parts) or None, "images": images, "upload_id": uid}
    run = pipeline.Run(pipeline.new_run_id(case_id))
    run.status("queued", "Queued")
    _start_run(run, inputs, deep_image, audit, _team())
    return {"run_id": run.id}


@app.get("/api/runs")
def list_runs():
    out = []
    for d in sorted(paths.RUNS.iterdir(), reverse=True):
        st = d / "status.json"
        if st.exists():
            s = json.loads(st.read_text(encoding="utf-8"))
            s.pop("events", None)
            out.append({"run_id": d.name, **s})
    return out


@app.get("/api/runs/{run_id}")
def get_run(run_id: str):
    run = pipeline.Run(run_id)
    if not (run.dir / "status.json").exists():
        raise HTTPException(404)
    inputs = run.read("inputs.json") or {}
    if inputs:
        inputs = dict(inputs)
        if inputs.get("upload_id"):
            inputs["image_urls"] = [f"/api/uploads/{inputs['upload_id']}/{Path(p).name}" for p in inputs.get("images", [])]
        else:
            inputs["image_urls"] = [f"/api/cases/{inputs['case_id']}/file/{Path(p).name}" for p in inputs.get("images", [])]
    ev = run.read("eval.json")
    return {
        "run_id": run_id, "status": run.read("status.json"), "inputs": inputs, "profile": run.read("profile.json"),
        "screening": run.read("screening.json"), "coverage": run.read("coverage.json"),
        "validation": run.read("validation.json"),
        "eval": {k: v for k, v in (ev or {}).items() if k == "local"} | (
            {"judge": {k: v for k, v in ev["judge"].items() if k in ("label", "precision", "recall", "f2", "tp",
                                                                     "n_submitted", "n_expected", "per_regulation")}}
            if ev and "judge" in ev else {}),
    }


@app.get("/api/runs/{run_id}/requirements")
def run_requirements(run_id: str):
    return pipeline.Run(run_id).read("requirements.json") or []


@app.post("/api/runs/{run_id}/export")
def export_run(run_id: str, body: dict):
    run = pipeline.Run(run_id)
    cands, inputs = run.read("candidates.json"), run.read("inputs.json")
    if cands is None:
        raise HTTPException(409, "run has no candidates yet")
    thr = float(body.get("threshold", inputs["config"]["threshold"]))
    sub = pipeline.finalize(run, cands, body.get("team_id") or _team(), inputs["case_id"], thr)
    rep = _validate_into(run)
    return {"n_requirements": len(sub["requirements"]), "threshold": thr, "validation": rep}


@app.get("/api/runs/{run_id}/submission.json")
def download_submission(run_id: str):
    f = pipeline.Run(run_id).dir / "submission.json"
    if not f.exists():
        raise HTTPException(404)
    return FileResponse(f, media_type="application/json", filename=f"{run_id}-submission.json")


@app.post("/api/runs/{run_id}/review")
def review(run_id: str, body: dict):
    """Append-only engineer review actions (accept / reject / comment)."""
    run = pipeline.Run(run_id)
    log = run.read("reviews.json") or []
    log.append({**body, "t": dt.datetime.now(dt.timezone.utc).isoformat()})
    run.write("reviews.json", log)
    return {"ok": True}


@app.get("/api/runs/{run_id}/reviews")
def reviews(run_id: str):
    return pipeline.Run(run_id).read("reviews.json") or []


# ------------------------------------------------------------------------------------------- regulations & documents
@app.get("/api/regulations")
def regulations():
    out = []
    for e in paths.index():
        vs = {v["role"]: v for v in e["versions"]}
        out.append({
            "regulation": e["regulation"], "title": e.get("title"), "source_url": e.get("source_url"),
            "base": {k: vs["base"].get(k) for k in ("version_label", "status", "title")},
            "latest": {k: vs["latest"].get(k) for k in ("version_label", "status", "title")} if "latest" in vs else None,
            "freshness": "newer_version_in_package" if "latest" in vs else "no_newer_in_package",
        })
    return out


def _doc_pdf(reg: str, role: str) -> Path:
    if reg.startswith("subgoal-"):
        f = paths.subgoal_dir(reg) / f"{role}.pdf"
        if not f.exists():
            raise HTTPException(404)
        return f
    try:
        return paths.pdf_path(reg, role)
    except KeyError:
        raise HTTPException(404)


def _parsed(reg: str, role: str) -> dict:
    if reg.startswith("subgoal-"):
        return ingest.load_file(_doc_pdf(reg, role), reg, role, "")
    return ingest.load(reg, role)


@app.get("/api/doc/{reg}/{role}/meta")
def doc_meta(reg: str, role: str):
    d = _parsed(reg, role)
    return {"regulation": reg, "role": role, "version_label": d["version_label"], "page_count": d["page_count"],
            "sha256": d["sha256"]}


@app.get("/api/doc/{reg}/{role}/outline")
def doc_outline(reg: str, role: str):
    d = _parsed(reg, role)
    return [{"label": p["label"], "title": p["title"][:120], "page": p["page"], "kind": p["kind"]}
            for p in d["paragraphs"] if p["kind"] in ("section", "annex", "part", "appendix") or p["num"].count(".") <= 1]


@app.get("/api/doc/{reg}/{role}/paragraph")
def doc_paragraph(reg: str, role: str, label: str):
    d = _parsed(reg, role)
    hits = [p for p in d["paragraphs"] if p["label"] == label]
    if not hits:
        raise HTTPException(404)
    p = hits[0]
    return {"label": p["label"], "text": p["text"], "pages": p["pages"]}


@app.get("/api/doc/{reg}/{role}/pdf")
def doc_pdf(reg: str, role: str):
    return FileResponse(_doc_pdf(reg, role), media_type="application/pdf")


@lru_cache(maxsize=64)
def _open(path: str) -> pymupdf.Document:
    return pymupdf.open(path)


@app.get("/api/doc/{reg}/{role}/page/{page}.png")
def doc_page(reg: str, role: str, page: int, label: str = "", q: str = "", zoom: float = 1.6):
    pdf = _doc_pdf(reg, role)
    doc = _open(str(pdf))
    if page < 1 or page > doc.page_count:
        raise HTTPException(404)
    pg = doc[page - 1]
    rects = []
    if q:
        words_ = q.split()
        for n in (14, 10, 7, 5):  # longest verbatim probe that is found on this page
            probe = " ".join(words_[:n])
            if len(probe) < 12:
                break
            found = pg.search_for(probe)
            if found:
                rects = found
                # extend: also highlight the rest of the quote if it continues on following lines
                rest = " ".join(words_[n:n + 10])
                if rest:
                    rects += pg.search_for(rest)
                break
    if not rects and label:
        d = _parsed(reg, role)
        for p in d["paragraphs"]:
            if p["label"] == label:
                rects = [pymupdf.Rect(*r[1:]) for r in p["rects"] if r[0] == page]
                break
    for r in rects:
        annot = pg.add_highlight_annot(r)
        annot.set_colors(stroke=(0.153, 0.855, 0.761))  # mint-400
        annot.update()
    pix = pg.get_pixmap(matrix=pymupdf.Matrix(zoom, zoom), annots=True)
    for a in list(pg.annots() or []):  # keep the cached document clean
        pg.delete_annot(a)
    return Response(pix.tobytes("png"), media_type="image/png", headers={"Cache-Control": "no-store"})


# ------------------------------------------------------------------------------------------- sub-goal
@app.post("/api/subgoal")
def start_subgoal(body: dict):
    from certi import subgoal
    case_id = body.get("case_id", "subgoal-dev")
    run_id = f"{case_id}-{dt.datetime.now().strftime('%Y%m%d-%H%M%S')}"
    out = SUBGOAL_RUNS / run_id
    out.mkdir(parents=True, exist_ok=True)
    (out / "status.json").write_text(json.dumps({"stage": "running"}), encoding="utf-8")

    def work():
        try:
            llm.run(subgoal.analyse(case_id, body.get("team_id") or _team(), out))
            (out / "status.json").write_text(json.dumps({"stage": "completed"}), encoding="utf-8")
        except Exception as exc:
            traceback.print_exc()
            (out / "status.json").write_text(json.dumps({"stage": "failed", "message": str(exc)}), encoding="utf-8")

    threading.Thread(target=work, daemon=True).start()
    return {"run_id": run_id}


@app.get("/api/subgoal")
def list_subgoal():
    out = []
    for d in sorted(SUBGOAL_RUNS.iterdir(), reverse=True):
        if d.is_dir() and not d.name.startswith("_"):
            st = json.loads((d / "status.json").read_text(encoding="utf-8")) if (d / "status.json").exists() else (
                {"stage": "completed"} if (d / "changes.json").exists() else {"stage": "unknown"})
            out.append({"run_id": d.name, **st})
    return out


@app.get("/api/subgoal/{run_id}")
def get_subgoal(run_id: str):
    d = SUBGOAL_RUNS / run_id
    if not d.exists():
        raise HTTPException(404)
    rd = lambda n: json.loads((d / n).read_text(encoding="utf-8")) if (d / n).exists() else None
    al = rd("alignment.json") or {}
    case_id = al.get("case_id") or ("subgoal-" + run_id.split("-")[1] if run_id.startswith("subgoal-") else run_id)
    return {"run_id": run_id, "case_id": case_id, "status": rd("status.json"), "alignment": rd("alignment.json"),
            "changes": rd("changes.json")}


@app.get("/api/subgoal/{run_id}/changes.json")
def download_changes(run_id: str):
    f = SUBGOAL_RUNS / run_id / "changes.json"
    if not f.exists():
        raise HTTPException(404)
    return FileResponse(f, media_type="application/json", filename=f"{run_id}-changes.json")


# ------------------------------------------------------------------------------------------- misc
@app.get("/api/usage")
def usage():
    return {"total_usd": round(llm.total_spent(), 3), "model": llm.MODEL}


WEB = paths.ROOT / "web" / "dist"
if WEB.exists():
    app.mount("/", StaticFiles(directory=WEB, html=True), name="web")
