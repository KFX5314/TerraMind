# Held-out main-goal F2 evaluation handoff

This branch starts at `main-f2` (`51eba8a`) and contains the offline held-out front-bumper evaluation. The extraction pipeline is unchanged. The official, user-reported score for [`eval-balanced-source-faithful.json`](../artifacts/evaluations/heldout-f2-offline-alternatives-20261025/eval-balanced-source-faithful.json) is **F2 61.2%, precision 34.9%, recall 75.5%** (450 requirements). Its local SHA-256 is `9c4cbac94ffe34f6ac031744f277d1aade0ce46153f648b2a4d4175725b6b936`. The organizer did not provide an upload-side hash, so the score-to-file association relies on the reported upload and locally matching backup.

## Progress and evidence

| Official F2 | What changed | Qualification |
| --- | --- | --- |
| 54.6% | Initial held-out upload; precision about 39.3%, recall 60.6%. | The exact uploaded file/hash is unknown. |
| 59.1% | A 479-item recovery file added nine source-supported requirements to the saved 470-item run; precision 32.4%, recall 74.5%. | The score improvement cannot be assigned solely to those additions because the first upload is unidentified. |
| 61.2% | The 450-item balanced, source-faithful file removed 30 unsupported or procedural items, added one R127 impact tolerance, corrected an R10 citation and two EMC descriptions, and restored the source's `should` wording in two R42 clauses. | Precision 34.9%, recall 75.5%; this is the current scored baseline. |

The later 438-item intermediate received a reported official **61.0% F2** (35.4% precision, 74.5% recall), so the 450-item file remains the best scored reference. See `heldout_findings.md`, `heldout_round2_findings.md`, `heldout_offline_alternatives_report.md`, and `independent_360_verification_report.md` for evidence and limits. The corresponding `artifacts/evaluations/heldout-f2-*/` folders contain saved candidates and per-ID change ledgers. The 394-, 360-, 449-, 451-, and 452-item candidates have no official score. The post-438 local comparison is in `artifacts/evaluations/heldout-f2-post438-20261025/offline-evaluation.json`.

## Offline checks (no Claude API calls)

From the repo root, with Python and `pymupdf` installed:

```powershell
python analysis/offline_verify.py
python ../industrial-ai-hackathon/tools/validate.py artifacts/evaluations/heldout-f2-offline-alternatives-20261025/eval-balanced-source-faithful.json --index ../industrial-ai-hackathon/regulations/index.json --strict
```

`offline_verify.py` only reads saved files, checks hashes and requirement counts, and prints candidate differences. The organizer validator checks schema and citations, **not** hidden requirement matches. The F2/precision/recall numbers above are official feedback, not scores reproducible offline. The `analysis/build_*.py`, `audit_479.py`, and `independent_verify_360.py` scripts document how candidates and audits were produced from saved extraction data and local PDFs. Some use absolute paths from the original workspace and create output directories exclusively; update those paths and use a fresh output location before rerunning them. Do not rerun them over the scored file. Do not use `python -m certi score --judge` for this workflow: the judge invokes a model.

## Required local inputs

The official organizer checkout is expected as sibling `../industrial-ai-hackathon/` (remote: `https://github.com/Certivity/industrial-ai-hackathon.git`). Its validator and index are under `tools/validate.py` and `regulations/index.json`. Downloaded regulatory PDFs are expected under `../industrial-ai-hackathon/regulations/pdf/<regulation_slug>/base/`. The saved extraction run used by several audit/build scripts is expected in a TerraMind checkout at `artifacts/runs/heldout-v1/` (especially `requirements.json`); those scripts currently point to the original `../TeraMind/TerraMind/` checkout. The organizer repository, PDFs, `.env`, caches, and hidden `expected.json` are deliberately outside this branch.

## Quality issues and next steps

- Product-conditional lamp and reflector functions remain in the 450-item file; the bumper spec does not establish every function or lamp category. Verify the actual hardware and regulatory scope before removing more requirements.
- Saved extraction conditions are not always carried into exported requirement text. Check whether this broadens obligations and hurts precision.
- Some citations need contextual PDF review, including table/section boundaries; the 450-item R48 reflector citation `R-0637` points to page 56 while the obligation text is on page 57.
- R94 vehicle-occupant outcomes and R127/GTR9 overlap remain uncertain. Do not infer the extra regulation from aggregate precision alone.
- Review the unscored 449/451/452 source-correction candidates against the 450-item baseline before any further upload. The 394/360 variants remove many possibly valid lighting obligations and carry material recall risk. Use the scored 450-item file as the rollback reference; the platform counts the last valid upload.

Only official platform feedback can establish whether a new candidate improves F2. Preserve the scored JSON byte-for-byte.
