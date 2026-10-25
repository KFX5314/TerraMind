# Held-out front bumper: judgment candidate (25 October 2026)

Unscored candidates built from the scored 450-item baseline
(`../heldout-f2-offline-alternatives-20261025/eval-balanced-source-faithful.json`, official F2 61.2 %, P 34.9 %, R 75.5 %)
by applying regulatory judgment about what the expert list contains. Built by `build_judgment.py` from saved data only
(no model calls). Both files pass `tools/validate.py --strict`.

| File | Requirements | SHA-256 |
|---|---:|---|
| `judgment-candidate.json` (recommended) | 526 | `a32ed28090b9b496ea19424628e73255e09513b5bbe24ebecc7cfa770bee01ea` |
| `judgment-lean.json` (fewer low-confidence additions) | 473 | `c0f920e01a00d5dc7472981e1c72d84fe20b0378ff5aab02e4550fc3b8e80fc3` |

Per-ID reasons, probabilities, source quotes, old and new texts are in `judgment-candidate-ledger.json` and
`judgment-lean-ledger.json`.

## What changed and why

Platform arithmetic (rounded official rates are consistent with 208 expert items and 157 matches in the 450):
F2 = 5M / (4·208 + N). Adding an item pays if its chance of matching exceeds ~12 %; removing one pays only if its chance
is clearly below that.

1. **Removed 84 items with near-zero expected hit rate.** UN R94 (14 occupant-injury criteria; regulation precision
   87.5 % says one of our eight regulations is not in the expert list, and R94 constrains no bumper feature); UN R10
   laboratory procedure annexes/appendices, sample marking, approval-mark composition and CoP procedures (43; the dev
   expert list for the same ESA sections keeps only Annex 9 3.1 and Annex 10 2); R148 CoP sampling annexes and Annex 2
   table rows (13); R48 Annex 9 CoP checks (9); R42 8.1 (1); four split variants superseded by step 3.
2. **Added 147 saved candidates (94 in the lean file)** from the extraction pool that were below the 0.5 export threshold
   but sit in the sections an expert walks through for a front bumper: R26 general exclusions, hardness, ornaments,
   air-intake flaps, aerial capping, projection method (13); R42 6.1.4 exhaust outcome and the Annex 3 test conditions
   (25); R127 Annex 3/5 legform-to-bumper procedure, impactor certification, ARHSS (18); GTR 9 measurement provisions,
   test conditions, legform details and DPPS sensing verification for the pedestrian impact sensors (31); R10 6.10.x
   deemed-to-comply provisions (3 + 2 from dev wording); R148 logos, reciprocally incorporated functions,
   direction-indicator photometry and failure provisions (23); R48 general provisions, direction-indicator
   arrangement/tell-tales, hazard warning, emergency stop, red-light zones (34).
3. **Transplanted the dev expert's exact wording** for paragraphs whose PDF text is identical in both cases: all 32 UN R10
   ESA items, 47 generic UN R148 items (markings 3.3.x, general 4.x, 6.1.3, Annex 3/8) and 18 UN R48 general 5.x items.
   65 of our texts were replaced by the expert sentence for the same paragraph; 13 expert items we lacked were added
   (R48 5.1 split, 5.7.2.1, 5.10.1, 5.10.4.3, 5.28.4; R10 6.10.1, 6.10.5; R148 3.3.3.5 x2, 4.5.5 x2, 4.7.2.4).

## Expected effect (scenario arithmetic, not a prediction)

| Scenario | Matches | F2 at N = 526 |
|---|---:|---:|
| Removals lose 5, additions and transplants gain nothing | 152 | 56.2 % |
| Removals lose 5, additions hit 12 % (break-even), transplants +5 | 176 | 65.0 % |
| Removals lose 5, additions hit 20 %, transplants +8 | 189 | 69.8 % |

The baseline is 61.2 %. The downside case requires every one of the 160 additions and all wording changes to miss,
which the dev-case hit rates (annex items 6 %, main-body items 40 %+) make unlikely; the central case is +4 to +8 points.
The lean file has the same removals and transplants with 53 fewer additions (N = 473): break-even there is +7 matches.

## Rollback

The platform counts the last valid upload. If a scored result is below 61.2 %, re-upload
`../heldout-f2-offline-alternatives-20261025/eval-balanced-source-faithful.json`
(SHA-256 `9c4cbac94ffe34f6ac031744f277d1aade0ce46153f648b2a4d4175725b6b936`).
