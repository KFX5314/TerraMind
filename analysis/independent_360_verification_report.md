# Independent offline verification of the 360-item held-out candidate

25 October 2026. Scored baseline: **450 requirements, F2 61.2%, recall 75.5%, precision 34.9%**. The 450-item local file has SHA-256 `9c4cbac94ffe34f6ac031744f277d1aade0ce46153f648b2a4d4175725b6b936`. The 360-item candidate has SHA-256 `02500e7caaab14aa63bd7ee3a0e509f557a781b4f6aeb34c98005af6b4931a5b`. Product evidence was the held-out `spec.md` and its exploded drawing, which labels a signalling strip on the **front corner** but does not identify its regulatory lamp category or every vehicle-level component. No hidden expected requirements or external model were used.

## Full removal audit

`artifacts/evaluations/heldout-f2-independent-20261025/removal-audit.json` contains a separate record for **each of the 92 removed IDs**, with component/function, specification status, drawing evidence, source modality and citation, saved extraction condition, whether the 394-item file retained it, and classification. The grades are evidence judgments, not hidden labels.

| Grade | Count | What the evidence establishes |
|---|---:|---|
| A — clearly inapplicable or redundant | **1** | R26 `R-0361` concerns a liquid-fuel tank filler cap. The product labels the part as an EV charge-port cover. |
| B — probably inapplicable | **14** | Thirteen front/side retro-reflector duties and one active ride-height suspension duty. Neither is identified in the spec/drawing. R48 side reflectors may become mandatory for a vehicle longer than 6 m; length is unknown. Front reflectors can also become mandatory with concealable forward lamp reflectors. |
| C — uncertain, potentially valid | **77** | 45 front-position/DRL duties, 22 front/other-indicator duties, seven production/inspection steps, and three active pedestrian-device duties. Their hardware or process is unspecified rather than contradicted. |
| D — likely valid, should be restored | **0** | The drawing does not prove a front-indicator, DRL, position, or active-protection configuration, so no removed variant is declared definitely applicable. **All C items should nevertheless be restored in a low-risk candidate.** |

The 394-item candidate removes **13 B + 43 C** items. The 360-item candidate additionally removes **1 A + 1 B + 34 C**. This is why neither large reduction is source-grounded as a *safe* precision improvement.

Source checking found saved quotes contiguous on the cited page for **76/92** removals. Fifteen other quotes use PDF table layout, composite text, or a page split. One confirmed citation defect is R48 `R-0637`: its number-of-front-reflectors sentence is on PDF **page 57**, while the 450-item file cites the preceding section heading on page **56**. The obligation itself is supported by the source when its conditional scope applies; a bad page does not make all reflector obligations inapplicable. No other removed claim was established as fabricated. Source support and product applicability are separate findings.

### Critical recall risks

* **Lighting (67 items):** The 360 file removes 45 front-position/DRL and 22 front/other-direction-indicator requirements. The drawing's front-corner “(Side) Lighting (signalling)” strip could be multifunctional. R48 makes front position and DRLs mandatory at vehicle level; whether this bumper carries those functions is unknown. R148 photometric, visibility, colour, marking and Annex 6 heat-test duties are independently testable when the lamp function exists. The 394 file already removes 43 of the front-position/DRL items.
* **Production procedures (7 items):** R48 Annex 9 and R148 Annexes 4/5 contain separate inspection or sampling actions. They are not proved duplicates merely because a product limit appears elsewhere.
* **Pedestrian protection (4 items):** Three R127/GTR9 active-device clauses are conditional; pedestrian impact sensors are shown, while a deployable protection device is unspecified. The removed R127 ARHSS clause concerns a separate vehicle-level ride-height system and is less likely to apply. R127 legform performance limits and R42 low-speed bumper impacts remain in all candidates.
* **Other regulations:** R10 EMC and R42 protective-device sets are unchanged between 450, 394, and 360. R26 loses only the EV fuel-filler misapplication. R94 frontal-crash criteria remain. All eight regulation labels remain, so the earlier regulation-level precision does not identify which regulation, if any, is extra.

## Two added UN R148 requirements

Both additions are in R148 **version 1.6.0**, are absent from the 450 file, and have their original source quote on the cited PDF page:

| ID | PDF citation | Source duty | Applicability limit |
|---|---|---|---|
| `R-0940` | p. 7, §3.3.2.5.1.3 | A category-6 direction indicator shows `R` or `L` to identify vehicle side. | Side lamp must be category 6; not established by the input. |
| `R-1152` | p. 47, Annex 8 §2.1/Table A8-1 | Category-5/6 indicator intensity distribution is additionally checked **0.2 s** after switch-on at **H5,V0**. | Side lamp must be category 5 or 6; its category is unknown. The table row and paragraph lead-in together support the text. |

No numerical limit, version, page, or paragraph was changed from the saved source-based extraction. These are defensible conditional additions, not guaranteed hidden matches.

## F2 break-even calculation

For one-to-one matching, `F2 = 5 TP / (4 G + N)`, where `N` is submitted requirements and `G` is hidden expected requirements. Rounded official precision and recall imply approximately `TP = 450 × 0.349 ≈ 157.1` and `G = TP / 0.755 ≈ 208.0`. Let `L` be baseline true matches lost by removals and `A` be true matches gained by additions. These are **hypothetical match counts**, not known platform labels.

| Candidate | `N` | Change | When it falls below the 450 baseline, approximately |
|---|---:|---|---|
| 394 | 394 | 56 removed, none added | **7 or more** removed items were true matches. |
| 360 | 360 | 92 removed, 2 added | **12** removed matches if neither addition matches; **13** if one matches; **14** if both match. Eleven lost matches with no addition is borderline because official percentages are rounded. |
| New 438 | 438 | 14 removed, 2 added | **2** removed matches if neither addition matches; **3** if one matches; **4** if both match. |

For illustration only, with **zero** removed true matches, the formula gives about **64.1%** for 394, **65.9%** for 360 with neither addition matched, and **61.8%** for 438 with neither addition matched. Losing 12 true matches would make 360 about **60.8%** if neither addition matched. These are arithmetic scenarios, **not predicted leaderboard scores**. The 77 uncertain removals make a 12-match loss plausible enough that 360 is not a safe upload.

## Recommended JSON and validation

The confirmed **450-item** file remains the safest final choice until a new file is scored. If there is time for one manual test and rollback, use the new **438-item intermediate**. It restores all 77 C items from the 360 file, removes only the 13 B reflector items plus the A fuel-cap mismatch, and retains the two source-verified conditional side-indicator additions. It leaves every R10, R42, R94, R127 and GTR9 requirement from the scored baseline intact. It also retains the front-position/DRL/front-indicator annex duties and all original mandatory lamp markings.

**Candidate:** `C:\Users\saish\Certivity\main-f2-eval\artifacts\evaluations\heldout-f2-independent-20261025\verified-intermediate-438.json`

**SHA-256:** `5e336e65e02b1211308c09a2a67dab7e485569a308bdc7459172f3cba92da30f`

The official strict validator returned `OK: verified-intermediate-438.json is valid (438 requirements)`. Team ID is `team-10`; case ID is `heldout-front-bumper`; all 438 IDs are unique; every cited regulation version matches the supplied base-version index; all cited PDF pages exist. In the 438 file, 378 saved source quotes match contiguously on the cited page, 42 have a prefix there, and 18 require table/section/page-split interpretation. The validator verifies schema and citation fields, not hidden applicability.

```powershell
& 'C:\Users\saish\Certivity\TeraMind\TerraMind\.venv\Scripts\python.exe' 'C:\Users\saish\Certivity\industrial-ai-hackathon\tools\validate.py' 'C:\Users\saish\Certivity\main-f2-eval\artifacts\evaluations\heldout-f2-independent-20261025\verified-intermediate-438.json' --index 'C:\Users\saish\Certivity\industrial-ai-hackathon\regulations\index.json' --strict
```

**Rollback:** `C:\Users\saish\Certivity\main-f2-eval\artifacts\evaluations\heldout-f2-offline-alternatives-20261025\eval-balanced-source-faithful.json` (SHA-256 `9c4cbac94ffe34f6ac031744f277d1aade0ce46153f648b2a4d4175725b6b936`). It is the unchanged locally verified 450-item file corresponding to the user-reported 61.2% upload. The leaderboard counts the last valid upload. No upload, push, merge, paid API, or working-application edit was performed.
