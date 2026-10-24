# HackathonbUVC: Certivity Requirements Agent

From a product specification and/or exploded view to the UN-Regulation requirements it must fulfil, each one cited
with regulation, version, page and paragraph and linked to the highlighted source passage. A second flow shows which
requirements must change when a regulation is amended.

## How it works

```
spec / drawing ──► 1 Product understanding (Claude vision+text, facts tagged spec_stated / observed / inferred / unknown)
                   2 Applicability screening of all 56 regulations in regulations/index.json (scope text + transitional provisions)
regulation PDFs ─► 0 Deterministic parser (PyMuPDF): paragraph tree, gold-format labels ("Annex 9 3.1"), physical pages, line boxes
                   3 Section-by-section extraction: atomic, near-verbatim obligations; label chosen from the supplied list,
                     verbatim quote; page/version resolved in code (never by the model)
                   4 Independent omission audit per section (second pass), dedup, export at a measured threshold
                   5 Export → organizer validate.py → engineer UI (requirement ↔ highlighted PDF page)

old reqs + old/new PDF ─► align each old requirement's source sentence anywhere in the new text (handles renumbering),
                          word diff → unchanged / modified / removed (+ reason); Claude rewrites modified texts and
                          splits genuinely new text into atomic "added" requirements
```

Inference never reads `expected.json`. Evaluation (`certi score`, `certi.subgoal_score`) runs afterwards and is
labelled as an internal estimate; the platform score is the real one.

## Setup (Windows / PowerShell or Git Bash)

```powershell
git clone https://github.com/Certivity/industrial-ai-hackathon.git      # organizer package (ignored by git)
python -m venv .venv
.venv\Scripts\python -m pip install pymupdf anthropic fastapi "uvicorn[standard]" jsonschema python-dotenv python-multipart
.venv\Scripts\python industrial-ai-hackathon\tools\fetch_regulations.py
copy .env.example .env      # then paste ANTHROPIC_API_KEY and TEAM_ID
.venv\Scripts\python -m certi parse                                   # parse all regulation PDFs (cached in data/)
cd web; npm install; npm run build; cd ..
.venv\Scripts\python -m uvicorn server.app:app --port 8765            # UI at http://127.0.0.1:8765
```

## CLI

```powershell
.venv\Scripts\python -m certi run --case dev-rear-lamp                 # main goal; writes artifacts/runs/<id>/submission.json
.venv\Scripts\python -m certi export --run-id <id> --threshold 0.5     # re-export with another threshold (no model calls)
.venv\Scripts\python -m certi score --run-id <id> --judge              # dev only: offline scorer + internal judge
.venv\Scripts\python -m certi subgoal --case subgoal-dev               # sub-goal; writes artifacts/subgoal/<id>/changes.json
.venv\Scripts\python -m certi validate <file> [--requirements-old F]   # organizer validator
```

All model calls are cached on disk by request hash (`data/cache/`), so re-running a run resumes for free.
Cost and usage of every call are logged to `data/usage.jsonl`.

## Sunday runbook (held-out case released 08:00, uploads close 13:00)

1. `git -C industrial-ai-hackathon pull --ff-only` (or unzip the held-out package into it) and
   `python industrial-ai-hackathon\tools\fetch_regulations.py`; then `python -m certi parse`.
2. Check the case folder name under `cases/` (e.g. `heldout-front-bumper`) and the sub-goal folder under `subgoal/`.
3. `python -m certi run --case heldout-front-bumper` and `python -m certi subgoal --case subgoal-heldout`.
4. Validate both files, look at the requirements in the UI, upload. **The last valid upload counts**:
   keep `artifacts/` (every candidate file with its hash) and upload the chosen file last.

## Measured on the worked examples (internal estimates)

See `docs/results.md`.

## Repository layout

- `certi/` pipeline package (parser, prompts, Claude wrapper, pipeline, sub-goal, evaluation, CLI)
- `server/` FastAPI backend for the UI; `web/` React UI styled with Certivity's palette
- `prompts/` static granularity examples; `scripts/` helpers
- `industrial-ai-hackathon/` organizer checkout (ignored), `data/` and `artifacts/` local outputs (ignored)

The participant data is restricted to hackathon use and is not included in this repository.
