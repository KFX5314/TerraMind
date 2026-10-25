# Held-out front bumper after the 438-item official result

25 October 2026. The official 450-item file scored **F2 61.2%, P 34.9%, R 75.5%**. The subsequently uploaded 438-item file scored **F2 61.0%, P 35.4%, R 74.5%**. Both uploads cite the same eight regulations. All work here was offline, using saved extraction, product inputs and local PDFs; no hidden expected JSON exists.

## What the platform result establishes

The rounded rates are consistent with **157/208** expected obligations matched by the 450-item upload and **155/208** by the 438-item upload. The 438 file removed 14 items (13 reflector clauses and one fuel-filler clause) and added two side-indicator clauses. Therefore at least **two net true matches were lost**. Depending on whether zero, one, or two additions matched, **two to four of the removals** matched hidden answers. The data does not identify which IDs. Removing all reflectors again is not evidence-based.

The local package's `tools/score_local.py` only computes regulation/page metrics against a supplied `expected.json`; the held-out expected file is unavailable. Running it against the rear-lamp development expected file would be invalid. This round's deterministic offline evaluation is in `artifacts/evaluations/heldout-f2-post438-20261025/offline-evaluation.json`; it checks structure, source-page quotes, numerical equivalence, citations, identical-text duplicates and score arithmetic. **It cannot measure requirement F2.**

## New source-checked files

All begin with the scored 450-item file. All front and side reflector requirements, R10 EMC, R42 impact, R127 pedestrian, GTR9 legform and R94 crash requirements remain.

| File | Requirements | Changes against scored 450 | Strict validation |
|---|---:|---|---|
| `source-corrected-449.json` | 449 | Remove R26 `R-0361`, which concerns a liquid-fuel tank filler rather than the stated EV charging flap; correct R48 `R-0637` citation from PDF p.56 to the obligation text on p.57; render R148 category-5/6 photometric values in equivalent decimal notation in `R-1059` and `R-1060`. | Passed |
| **`side-signal-recovery-451.json`** | **451** | Same corrections, plus saved R148 `R-0940` category-6 R/L marking and `R-1152` category-5/6 0.2-second intensity check at H5,V0. Both are conditional on the lamp category. | **Passed** |
| `targeted-recovery-452.json` | 452 | Same as 451, plus saved R26 `R-0362` duty for *movable* air-intake/outlet flaps in every position of use. The grille/airflow function is specified, but movable flaps are not shown, making this the riskier addition. | Passed |

The saved source quote for each addition matches its cited PDF page: R148 version 1.6.0 p.7 §3.3.2.5.1.3, R148 p.47 Annex 8 §2.1/Table A8-1, and R26 version 4.0.0 p.8 §6.12.1. The R148 Table 8 numbers in `R-1059` and `R-1060` were checked arithmetically: `6×10⁻¹ = 0.6`, `5.0×10¹ = 50`, `2.80×10² = 280`, and `1.40×10² = 140` cd. The baseline had no identical-text duplicate within a regulation; neither new candidate introduces one. Full per-ID changes and reasons are in `change-ledger.json` and `side-signal-451-ledger.json`.

The offline check gives the 451 file **8 regulations, 102 distinct cited pages and 451 unique requirements**. Of its saved source quotes, 390 match contiguously on the cited page, 42 have a matching prefix and 19 need table/section/page-split interpretation. Those counts are provenance checks, not precision or recall. Its team ID is `team-10`, case ID `heldout-front-bumper`, and all versions match the supplied base-version index. The official validator returned `OK: side-signal-recovery-451.json is valid (451 requirements)`.

## F2 arithmetic, not a score prediction

Let `a` be the number of the two R148 additions that match and `l` be whether the removed R26 fuel-filler item matched. If the text/citation edits do not change matches, the 451 candidate has `TP = 157 + a − l`, and `F2 = 5 TP / (4×208 + 451)`.

| `a` | `l` | Hypothetical F2 |
|---:|---:|---:|
| 0 | 0 | 61.19% |
| 1 | 0 | 61.57% |
| 2 | 0 | 61.96% |
| 0 | 1 | 60.80% |

Wording changes may also change model matches. A **5–10 percentage-point** improvement is not supported by this small, source-grounded delta. A much larger gain would require identifying many false positives or recovering many true obligations, which cannot be inferred from the aggregate held-out scores alone.

## Recommendation

For **one manual development-platform test**, upload `side-signal-recovery-451.json`. It preserves the reflectors whose blanket removal lost matches, fixes one confirmed citation, normalizes two source-table limits, and adds only two duties tied to the pictured signalling function. The 452-item variant is available if the user later establishes movable grille shutters. The confirmed 450-item file remains the best scored fallback until a new upload proves better. Because the leaderboard counts the last valid upload, restore 450 before the deadline if 451 scores lower.

**Test file:** `C:\Users\saish\Certivity\main-f2-eval\artifacts\evaluations\heldout-f2-post438-20261025\side-signal-recovery-451.json`

**SHA-256:** `43803238fe71a453a109d7ba9f359fc01205eb3ce35781031f4f7c237041588c`

**Rollback (official 61.2%):** `C:\Users\saish\Certivity\main-f2-eval\artifacts\evaluations\heldout-f2-offline-alternatives-20261025\eval-balanced-source-faithful.json`, SHA-256 `9c4cbac94ffe34f6ac031744f277d1aade0ce46153f648b2a4d4175725b6b936`.

Validate with:

```powershell
& 'C:\Users\saish\Certivity\TeraMind\TerraMind\.venv\Scripts\python.exe' 'C:\Users\saish\Certivity\industrial-ai-hackathon\tools\validate.py' 'C:\Users\saish\Certivity\main-f2-eval\artifacts\evaluations\heldout-f2-post438-20261025\side-signal-recovery-451.json' --index 'C:\Users\saish\Certivity\industrial-ai-hackathon\regulations\index.json' --strict
```

The offline analysis did not upload or overwrite any submission, call a model API, merge code, or edit the working application.
