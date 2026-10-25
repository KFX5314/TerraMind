# TerraMind: Certivity Requirements Agent

TerraMind turns a product specification and exploded-view drawing into the list of UN-Regulation requirements the
product must fulfil. Each requirement is cited by regulation, version, page and paragraph, and the UI links it to the
highlighted source passage. A second flow takes an amended regulation and reports which existing requirements are
modified or removed, and which new ones must be added.

Built for the Certivity Industrial AI Hackathon (Munich, October 2026). The UI runs locally; see
[User interface](#4-user-interface).

---

## Final results

All files are in [`final_results/`](final_results/) and pass the organizer validator (`tools/validate.py --strict`).

| Challenge | Case | File | Official score |
|---|---|---|---|
| Main goal | held-out, front bumper | [`main-goal_heldout-front-bumper.json`](final_results/main-goal_heldout-front-bumper.json) (300 requirements) | final upload; previous best 360-item file: F2 **65.0%** (P 43.1%, R 74.5%), regulations R 100% |
| Sub-goal | held-out, UN R171 change | [`subgoal_heldout-regulation-change.json`](final_results/subgoal_heldout-regulation-change.json) (85 changes) | final upload; previous best 63-change file: flag recall **81.2%**, flag precision 82.5%, change accuracy 72.9% |
| Main goal | dev, rear lamp | [`main-goal_dev-rear-lamp.json`](final_results/main-goal_dev-rear-lamp.json) (373 requirements) | F2 **69.3%** (P 42.1%, R 82.6%), regulations 100% / 100% |
| Sub-goal | dev, UN R175 change | [`subgoal_dev-regulation-change.json`](final_results/subgoal_dev-regulation-change.json) (26 changes) | flag recall **100%**, flag precision 92.3%, change accuracy 69.6% |

Scores are the organizer platform's. How the held-out files were built, and what each platform result taught us, is
documented in [`analysis/heldout_final_upload.md`](analysis/heldout_final_upload.md).

---

## Technology

| Layer | Technology | Role |
|---|---|---|
| LLM | Claude **Opus 5.5** (`claude-opus-5-5`) via the Anthropic Python SDK | product understanding (vision + text), applicability screening, requirement extraction, sub-goal rewriting, relevance judging |
| Structured output | JSON-schema constrained outputs | every model answer is machine-checked JSON; paragraph labels come from an enum of the real labels, so citations cannot be invented |
| PDF parsing | **PyMuPDF** (deterministic, no model) | paragraph tree with gold-format labels (`6.9.1`, `Annex 9 3.1`, `Annex 4 Part 1 1.2`), physical pages, line boxes for highlighting; tables via `find_tables` |
| Backend | Python 3.12, **FastAPI** + Uvicorn | runs the same pipeline as the CLI in background jobs; serves PDFs, page images with highlights, results |
| Frontend | **React 19 + TypeScript + Vite** | projects and runs, requirement ↔ highlighted source page, regulation library, "Update Impact" (sub-goal) view |
| Validation | organizer `validate.py`, `jsonschema` | every export is validated before upload |
| Cost and reproducibility | disk cache by request hash (`data/cache/`), usage ledger (`data/usage.jsonl`), per-run budget (`MAX_RUN_USD`) | re-running a run is free; every call and its cost is logged |

## How it works

### Main goal: specification → requirements

```
spec.md + exploded_view.png ──► 1. Product profile (Claude vision+text; each fact tagged spec_stated / observed / inferred / unknown)
regulation PDFs ─────────────► 0. Deterministic parser (PyMuPDF) → paragraph tree, labels, pages, tables   [no model]
profile + scope text of all 56 regulations ──► 2. Applicability screening (Claude) → keep p ≥ 0.5
selected regulations ──► 3. 8,000-character sections (+ parent clauses, + tables as markdown)
                         → extraction per section (Claude): atomic, source-faithful obligations, verbatim source
                           sentence, paragraph label from an enum, probability, applicability
candidates ──► 4. Page resolved from the quote in code, exact source-aware dedupe, export at p ≥ 0.5 (annexes 0.6)
           ──► submission.json ──► validate.py ──► UI
```

The model never assigns page numbers or versions. Code resolves them from the verbatim quote, so every citation
points at real text in the PDF.

**Held-out refinement:** `analysis/judge_requirements.py` is a second Claude pass. It rates each exported
requirement with the probability that a regulatory expert would list it for this product. The cut-off (0.3) was
calibrated on the dev answer key, where it raised F2 from 0.693 to 0.708. The regulation flagged as superfluous by
the regulation-level score (UN R94) was removed.

### Sub-goal: regulation amendment → changed requirements

```
requirements_old.json + old.pdf + new.pdf
  ──► parse both PDFs, split into sentences and list items                                   [code]
  ──► per old requirement: locate its source in old.pdf → align to the best match anywhere   [code]
      in new.pdf (handles renumbering) → word diff with notation normalisation
        no match           → removed
        substantive diff   → modified: Claude writes the new text from the NEW source sentence;
                             guards keep unchanged wording and the source's modal verb ("may" stays "may")
        identical          → unchanged
  ──► new sentences that match nothing in old.pdf, in sections the old requirements cover    [code]
      → Claude splits them into atomic "added" requirements (one per modal verb)
  ──► changes.json (upload) + alignment.json (matching details, used by the UI)
```

Deciding which requirements changed is done entirely in code; Claude only writes the text. With
`CERTI_SUBGOAL_ANNEX=1`, new obligations in annexes are also considered. This is how the final held-out file was
produced.

---

## Run it

### 1. Prerequisites

- Python 3.12, Node.js 20 or newer, an Anthropic API key.
- The organizer package next to this repository (it is not redistributed here):

```powershell
cd ..
git clone https://github.com/Certivity/industrial-ai-hackathon.git
cd TerraMind
```

TerraMind looks for it at `./industrial-ai-hackathon`. If you keep it elsewhere, for example as a sibling folder,
set `CERTI_PACKAGE`:

```powershell
$env:CERTI_PACKAGE = "..\industrial-ai-hackathon"      # PowerShell
export CERTI_PACKAGE=../industrial-ai-hackathon        # bash
```

### 2. Install

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install pymupdf anthropic fastapi "uvicorn[standard]" jsonschema python-dotenv python-multipart pytest
.venv\Scripts\python ..\industrial-ai-hackathon\tools\fetch_regulations.py      # download regulation + sub-goal PDFs
copy .env.example .env                                                            # then fill in the values below
```

`.env`:

```
ANTHROPIC_API_KEY=sk-ant-...
TEAM_ID=team-10
CLAUDE_MODEL=claude-opus-5-5
MAX_MODEL_CONCURRENCY=8
MAX_RUN_USD=20          # a full main-goal run costs about $8-13
```

### 3. Command line

```powershell
.venv\Scripts\python -m certi parse                                         # parse all regulation PDFs (free, cached)
.venv\Scripts\python -m certi run --case heldout-front-bumper               # main goal → artifacts/runs/<id>/submission.json
.venv\Scripts\python -m certi export --run-id <id> --threshold 0.5          # re-export another threshold (no model calls)
.venv\Scripts\python -m certi subgoal --case subgoal-heldout --team team-10 # sub-goal → artifacts/subgoal/<id>/changes.json
$env:CERTI_SUBGOAL_ANNEX = "1"; .venv\Scripts\python -m certi subgoal --case subgoal-heldout --team team-10   # final sub-goal variant
.venv\Scripts\python -m certi validate <file> [--requirements-old <file>]   # organizer validator
.venv\Scripts\python analysis\judge_requirements.py <submission.json> <case_id> <ratings.json>  # relevance judge
.venv\Scripts\python -m pytest -q tests                                     # deterministic tests (no model calls)
```

Case IDs are the folder names in the organizer package, for example `dev-rear-lamp`, `heldout-front-bumper`,
`subgoal-dev` and `subgoal-heldout`. Model answers are cached, so re-running the same case is free and gives
identical output.

### 4. User interface

```powershell
cd web; npm install; npm run build; cd ..
.venv\Scripts\python -m uvicorn server.app:app --port 8765
```

Open http://127.0.0.1:8765. For frontend development, `npm run dev` in `web/` serves on port 5173 and proxies `/api`
to port 8765.

---

## Repository layout

| Path | Contents |
|---|---|
| `certi/` | pipeline package: `ingest.py` (PDF parser), `pipeline.py` (main goal), `subgoal.py` (sub-goal), `llm.py` (Claude wrapper, cache, budget), `prompts.py` / `extract_prompt.py`, `tables.py`, evaluation helpers |
| `server/` | FastAPI backend for the UI |
| `web/` | React + TypeScript + Vite frontend |
| `final_results/` | final submission files (table above) |
| `analysis/` | held-out evaluation scripts, judges, and reports |
| `artifacts/` | saved runs and evaluation candidates |
| `tests/` | deterministic tests |
| `docs/` | measured results and pitch |

Inference never reads `expected.json`. Local evaluation (`certi score`, `certi.subgoal_score`, the judges' dev
calibration) runs afterwards and is labelled as an internal estimate; the platform score is the official one. The
organizer data is restricted to hackathon use and is not included in this repository.
