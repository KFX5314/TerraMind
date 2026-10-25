# Held-out front-bumper F2: offline candidate comparison

25 October 2026. Analysis used only saved extraction artifacts, the held-out product specification and drawing, local regulation PDFs, deterministic scripts, and the official local validator. No model or network calls were made. No file was uploaded.

## Official baseline and limits of the evidence

The user-reported official score for the 479-requirement upload is **F2 59.1%, recall 74.5%, precision 32.4%**. The saved `verified-recovery.json` has the reported requirement count and size; its SHA-256 is `7d97af7fbececfdba7d5e12f878b023eaab66b7c42ccfb132cc05585098232f2`. `scored-479-rollback.json` is byte-identical to it. The platform upload hash was not available, so this identification rests on count, size, upload history and the saved file, not a platform-side hash comparison. The hidden requirement labels are unavailable: none of the candidates has a measured F2, precision or recall.

The per-requirement audit is in `artifacts/evaluations/heldout-f2-audit-20261025/requirement-audit.json`. It records source, saved extraction metadata and review flags for all 479 exports. It is a deterministic triage, not 479 independent expert legal determinations. Of 479 saved source quotes, 415 match as contiguous full text on the cited page and 468 have a matching prefix there. Eleven require manual context review due to table layout, composite quotation, or adjacent-page text. The clear page error is UN R10 `R-0029`: the test-method sentence is on PDF page 11, while the baseline cites page 10. The balanced variants fix this citation.

The saved extractor marked 288 of the 479 exported candidates as conditional. The submission schema does not expose a separate condition field, and some texts do not repeat the condition. This is a confirmed metadata loss with uncertain scoring impact. The only exact same-regulation text pair identified, R10 `R-0217` and `R-0239`, concerns different Annex 7 broadband and Annex 8 narrowband tests, so both are retained. Two R42 impact speeds (`R-0414`, `R-0420`) say “should” in the source but “shall” in the baseline. The source-faithful balanced variant fixes those modal verbs while retaining 4 km/h and 2.5 km/h and their tolerances.

## Candidate comparison

All paths below are under `C:\Users\saish\Certivity\main-f2-eval\artifacts\evaluations\heldout-f2-offline-alternatives-20261025` and have the official submission schema. Every file passed `tools/validate.py --strict` with the supplied regulation index.

| Candidate | File | Requirements | Added / removed / changed vs scored 479 | Expected trade-off, unscored |
|---|---|---:|---|---|
| Rollback | `scored-479-rollback.json` | 479 | 0 / 0 / 0 | Measured F2 59.1%; exact local copy of the scored file. |
| A: conservative scope | `eval-scope-conservative.json` | 437 | 1 / 43 / 0 | Best chance to remove unsupported lamp variants, but greatest risk of losing legitimate conditional obligations. |
| B: balanced | `eval-balanced.json` | 450 | 1 / 30 / 3 | Smaller scope cleanup; retains uncertain reflector, DRL and answer-back variants. Three changes are two EMC test-context clarifications and the R10 page correction. |
| B2: source-faithful balanced | `eval-balanced-source-faithful.json` | 450 | 1 / 30 / 5 | Same selection as B; additionally fixes two R42 “should”/“shall” mismatches. Recommended first manual test. |
| C: high recall | `eval-high-recall.json` | 487 | 8 / 0 / 0 | Adds source-backed test and side-indicator details; highest chance of further recall, with substantial precision risk from conditional and overlapping duties. |

Counts by regulation:

| Regulation | Scored | A | B / B2 | C |
|---|---:|---:|---:|---:|
| UN R10 | 81 | 81 | 81 | 81 |
| UN R26 | 26 | 26 | 26 | 26 |
| UN R42 | 20 | 20 | 20 | 20 |
| UN R48 | 156 | 117 | 130 | 156 |
| UN R94 | 14 | 14 | 14 | 14 |
| UN R127 | 25 | 26 | 26 | 31 |
| UN R148 | 127 | 123 | 123 | 129 |
| UN GTR 9 | 30 | 30 | 30 | 30 |

For every added or removed requirement, `change-ledger.json` records the ID, text, source citation, source quote, saved probability and applicability, and the reason. Its `modified` records cover B's three changes. `balanced-source-faithful-ledger.json` records B2's additional two changes. The added requirements' eight unique saved source quotes all match their cited PDF page. The official validator verifies schema and citation structure; it does not verify engineering applicability or hidden-gold matches. Four baseline quotes on removed items are composite/noncontiguous in text extraction and were reviewed against their cited context; they are not proof of bad citations.

### Reasons for changes

* A starts from the existing 441-item scope candidate and removes four more UN R148 conformity-of-production sampling and retest procedures (`R-1091`, `R-1092`, `R-1122`, `R-1130`). Relative to scored 479, it also lacks 39 R48 requirements for front fog (9), front/side retro-reflectors (7/6), cornering (11), and manoeuvring lamps (6). None of these five functions is identified in the product parts list or drawing, although generic “functional lighting” is listed. Consequently their absence is an inference, not proof of inapplicability; this is A's material recall risk. A adds the distinct R127 Annex 5 lower-legform horizontal **and** vertical ±10 mm impact tolerance (`R-0894`), saved probability 0.3, PDF page 33.
* B and B2 remove only the 26 front fog, cornering, and manoeuvring R48 items plus the four R148 procedural items. The potentially applicable R48 reflectors, daytime running lamps and answer-back signals remain, as do side-signalling requirements and mandatory/conditional R148 engineering markings. They add `R-0894`. They distinguish R10 Annex 7 broadband (`R-0217`) from Annex 8 narrowband (`R-0239`) rather than merging two independently testable duties, and correct `R-0029`'s PDF citation to page 11. B2 also changes the two R42 modal verbs to match the PDF, preserving the test-speed values.
* C retains every scored item and adds six saved R127 Annex 5 legform test conditions (`R-0894`, `R-0902`, `R-0904`, `R-0908`, `R-0909`, `R-0910`) and two conditional R148 side-indicator obligations (`R-0940`, `R-1152`). Their source quotes are present on the cited PDF pages. The upper-legform duties apply only when the vehicle geometry triggers that test; the side-indicator duties require the specified lamp category, which the product input does not establish. R127 and GTR9 may overlap. `R-1152` is a table-derived photometry condition whose full surrounding context requires interpretation, so exact quote presence is narrower evidence than independent applicability.

Other confirmed wording risk remains in A, B and C unless noted: the two R42 “should” to “shall” conversions. No regulation is deleted wholesale: the official 87.5% regulation precision with 100% regulation recall indicates one possible extra regulation among eight, but does not identify which. R94 and GTR9 applicability is unresolved. Deleting either based on that aggregate score would be speculative.

## Recommendation and rollback

**Test B2 first** if choosing one manual replacement. It removes the clearest cluster of unestablished lighting functions while preserving uncertain variants and all current bumper crash, sensing, structural and technical annex coverage. Its source corrections avoid conflating distinct EMC tests and turning R42 guidance into a stronger legal duty. A is a more aggressive precision bet with larger recall risk; C would pursue recall after a score showed that precision is not the main constraint. No ≥65% score is promised. The last valid upload becomes the scored entry, so the user should inspect the result before any further upload.

Recommended absolute path: `C:\Users\saish\Certivity\main-f2-eval\artifacts\evaluations\heldout-f2-offline-alternatives-20261025\eval-balanced-source-faithful.json` (SHA-256 `9c4cbac94ffe34f6ac031744f277d1aade0ce46153f648b2a4d4175725b6b936`).

Official strict validation command in PowerShell:

```powershell
& 'C:\Users\saish\Certivity\TeraMind\TerraMind\.venv\Scripts\python.exe' 'C:\Users\saish\Certivity\industrial-ai-hackathon\tools\validate.py' 'C:\Users\saish\Certivity\main-f2-eval\artifacts\evaluations\heldout-f2-offline-alternatives-20261025\eval-balanced-source-faithful.json' --index 'C:\Users\saish\Certivity\industrial-ai-hackathon\regulations\index.json' --strict
```

For a manual rollback, upload `C:\Users\saish\Certivity\main-f2-eval\artifacts\evaluations\heldout-f2-offline-alternatives-20261025\scored-479-rollback.json` (SHA-256 `7d97af7fbececfdba7d5e12f878b023eaab66b7c42ccfb132cc05585098232f2`). The existing scored JSON and prior 441-item candidate were left unchanged. No push, merge or upload was performed.
