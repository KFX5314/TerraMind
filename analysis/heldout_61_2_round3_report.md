# Held-out front-bumper: offline round after 61.2% F2

25 October 2026. The user reported **61.2% requirement F2** after manually uploading the 450-item `eval-balanced-source-faithful.json`. The scored precision and recall were not yet provided. The local 450-item file has SHA-256 `9c4cbac94ffe34f6ac031744f277d1aade0ce46153f648b2a4d4175725b6b936`; this is the exact hash verified for the backup file earlier in this run, and the immutable copy remains at `artifacts/evaluations/heldout-f2-offline-alternatives-20261025/eval-balanced-source-faithful.json`. The platform has not supplied an upload hash, so the identification still rests on the user's upload description and matching local hash.

No hosted model, external API, development `expected.json`, UI change, push, merge, or upload was used. The original 450-item file remains unchanged. New files are in `artifacts/evaluations/heldout-f2-module-scope-20261025/` and are read-only.

## Findings and changes

The 450-item file still includes product-conditional lamp requirements that the supplied front-bumper specification and drawing do not establish:

* **39 R48 items** for front and side retro-reflectors (13), front position lamps (12), and daytime running lamps (14). The latter two are vehicle-level requirements when those lamp functions exist, but the product description does not place them in this bumper module. Reflectors are likewise absent; the saved screen excluded reflector device regulation R3 for that reason.
* **17 R148 items** for front-position/DRL photometry, DRL heat testing, function-specific visibility, and a front-position marking variant. General and side-signalling markings remain.
* **20 further R48/R148 items** for front direction-indicator variants. The named integrated function is *side* signalling; side-indicator and side-marker clauses remain. This is a stronger scope inference because a front bumper corner could conceivably contain a front indicator not separately labelled in the drawing.
* **Seven production-inspection or repeated sampling instructions** from R48 Annex 9 and R148 Annexes 4/5. The substantive lamp positioning, visibility, colour, photometric limits, and approval markings remain.
* **Nine more scope items**: front-position/DRL colour rules (2), a front-indicator area rule explicitly exempting side categories 5/6, an R148 photometric category list excluding side categories 5/6, optional active ride-height suspension, three active/deployable pedestrian-device clauses, and a liquid-fuel filler-cap projection clause applied to an EV charging flap. These are explicit product/function boundaries but could cost recall if the hidden product interpretation assumes additional equipment.

The 360-item candidate also adds two saved, source-verified **UN R148** side-indicator duties: category-6 R/L handed marking (`R-0940`, PDF page 7) and a category-5/6 luminous-intensity check 0.2 seconds after switch-on at H5,V0 (`R-1152`, PDF page 47). They are conditional on the actual lamp category, which the product input does not specify. Both original source quotes appear on their cited pages; the second also depends on the paragraph lead-in above its table row. No new obligation or citation was invented.

All **R94 frontal-crash requirements remain** in the recommended file. R94 might be the extra regulation implied by the prior aggregate regulation precision of 87.5%, but that score cannot identify it. The separate 355-item system-boundary variant removes 11 full-vehicle occupant-dummy criteria; it is a higher-risk probe and is *not* the recommended first upload. UN R10 EMC, R26 external projections, R42 bumper protective-device, R127 pedestrian impacts, and GTR9 legform duties also remain substantially intact.

## Candidates

| File | Requirements | Difference vs scored 450 | Intended trade-off | Strict validation |
|---|---:|---|---|---|
| `module-lamp-scope.json` | 394 | −56 | Safest new scope pruning; still retains front-indicator variants. | Passed |
| `module-side-signal-scope.json` | 374 | −76 | Adds front-indicator scope pruning; more recall risk. | Passed |
| `module-side-signal-procedure-trim.json` | 367 | −83 | Also removes seven repeated inspection/sampling instructions. | Passed |
| `module-evidence-358.json` | 358 | −92 | Adds explicit function and system-boundary corrections. | Passed |
| **`module-evidence-side-recovery-360.json`** | **360** | **−92, +2** | **Best evidence-based F2 test: precision cleanup plus two side-indicator recoveries.** | **Passed** |
| `module-system-boundary.json` | 355 | −95 | Removes 11 R94 occupant outcomes; high recall risk. | Passed |

The 360-item regulation counts are GTR9 **29**, R10 **81**, R26 **25**, R42 **20**, R48 **75**, R94 **14**, R127 **23**, and R148 **93**. All 360 IDs are unique. The 450-item baseline contains 130 R48, 123 R148, 26 R127, 30 GTR9, 26 R26, 20 R42, 81 R10, and 14 R94.

The change reasons and saved source metadata for each removal are in `change-ledger.json`, `procedure-trim-ledger.json`, and `module-evidence-358-ledger.json`; the two additions are in `module-recovery-360-ledger.json`. Relative to the 450 baseline, 76 of the 92 removed requirements have a contiguous saved source quote on the cited PDF page. The other 16 are composite quotes, table formatting, or split text and require contextual reading; they are not counted as proven invalid citations. The additions' source quotes match their cited PDF pages. The official validator checks structure and citation fields, not hidden-gold applicability.

**Recommended manual test:** `C:\Users\saish\Certivity\main-f2-eval\artifacts\evaluations\heldout-f2-module-scope-20261025\module-evidence-side-recovery-360.json`, SHA-256 `02500e7caaab14aa63bd7ee3a0e509f557a781b4f6aeb34c98005af6b4931a5b`.

The 61.2% score confirms that the preceding 450-item scope cleanup outperformed the 479-item file, but it does **not** establish that the new 92 removals are hidden false positives. The largest risk is that the unlisted lamp functions or active safety features are nevertheless expected. A 5–10 percentage-point F2 improvement cannot be asserted offline. If the 360-item test loses recall substantially, try the 394-item candidate or restore the scored 450-item file. The leaderboard counts the *last valid upload*.

Validate the recommended file with:

```powershell
& 'C:\Users\saish\Certivity\TeraMind\TerraMind\.venv\Scripts\python.exe' 'C:\Users\saish\Certivity\industrial-ai-hackathon\tools\validate.py' 'C:\Users\saish\Certivity\main-f2-eval\artifacts\evaluations\heldout-f2-module-scope-20261025\module-evidence-side-recovery-360.json' --index 'C:\Users\saish\Certivity\industrial-ai-hackathon\regulations\index.json' --strict
```

Rollback by manually uploading the byte-identical 450-item `C:\Users\saish\Certivity\main-f2-eval\artifacts\evaluations\heldout-f2-offline-alternatives-20261025\eval-balanced-source-faithful.json` (SHA-256 `9c4cbac94ffe34f6ac031744f277d1aade0ce46153f648b2a4d4175725b6b936`). Uploads were left to the user.
