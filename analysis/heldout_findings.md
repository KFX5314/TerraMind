# Held-out front-bumper offline audit (25 October 2026)

## Provenance boundary

No upload receipt, uploaded filename, platform hash, or scored manifest was found locally. The 54.6% F2, 60.6% recall, and 39.3% precision are user-reported official results; none of the local candidates has an official score. The two saved front-bumper submissions are:

| Saved run | Requirements | SHA-256 | Generated | Configuration |
|---|---:|---|---|---|
| `dry-front-bumper-v3` | 575 | `a0d762adbdcc1693d8574a0be4b29a453804a282891439fb8dce67c2d8c1edd2` | 2026-10-24 14:29:50 UTC | Opus 5.5, prompt v3, threshold 0.5, parser p8 |
| `heldout-v1` | 470 | `9a4032c68f56ef036fea417fdcf12ba9dc0f8388d068119fe1304cd6f1ae1729` | 2026-10-25 07:25:32 UTC | Opus 5.5, prompt v6, threshold 0.5, annex threshold 0.5, 8k chunks, parent context on, parser p8, audit off, deep image off |

All generated candidates below are **provisionally** based on `heldout-v1`. Its `submission.json` is preserved unchanged; `baseline.json` is byte-identical. The run did not record a Git commit hash. Commit `4e14e9b` predates the run and has the same main-goal code as current `main-f2` (`51eba8a` changes only sub-goal code), but an uncommitted runtime change cannot be ruled out. The runtime annex threshold 0.5 overrides the 0.6 default in `4e14e9b`.

## Confirmed local findings for `heldout-v1`

| Regulation | Extraction chunks | Raw candidates | Exported | Filtered at 0.5 |
|---|---:|---:|---:|---:|
| UN R10 | 44 | 330 | 81 | 249 |
| UN R26 | 7 | 47 | 26 | 21 |
| UN R42 | 5 | 47 | 18 | 29 |
| UN R48 | 38 | 365 | 156 | 209 |
| UN R94 | 19 | 69 | 14 | 55 |
| UN R127 | 12 | 57 | 18 | 39 |
| UN R148 | 18 | 247 | 127 | 120 |
| UN GTR 9 | 14 | 119 | 30 | 89 |
| **Total** | **157** | **1,281** | **470** | **811** |

All 157 jobs report `done`, with zero failed sections. The raw and post-deduplication candidate counts both equal 1,281: **zero candidates were removed by deduplication** in this run. The 470 exported IDs in `requirements.json` exactly match `submission.json`.

Screening selected eight regulations. Eleven more were marked applicable or potentially applicable but fell below the 0.5 cutoff; 37 were marked not applicable. UN R137 was explicitly classified `applicable` at 0.45 and therefore excluded. R137 covers M1 vehicles up to 3,500 kg in full-width frontal tests, distinct from R94 offset frontal tests. The product spec gives M1 but no mass or full-vehicle integration detail, so adding vehicle-occupant outcomes from R137 is a **possible**, not verified, improvement. R152 at 0.45 needs evidence that the bumper's camera/radar serves AEBS. R149 at 0.4 needs an actual road-illumination lamp such as a front fog or cornering lamp; the spec identifies decorative and side-signalling lamps only. Do not add these whole regulations by threshold alone.

Reconstructing chunks from the saved parser and table caches reproduced every saved chunk's paragraph-label set. R10 Annex 6 paragraph 2.1.1.2 was split mid-word at the 8k-character boundary; the effect on extracted bumper obligations is unproven. R127 had three detected tables, two attached; the unattached table is an approval information form on page 25. R42 had two detected and both attached. R148 had 24 detected and 19 attached; page 21 contains a continuation of a photometric table, but corresponding flattened PDF text and some extracted photometric candidates exist. There is no measured count of lost requirements from table attachment alone. GTR9's many unattached tables are predominantly preamble bibliography, not test limits.

R127 Annex 5 paragraphs 1.9 and 1.13 contain separate lower-legform test conditions (±5° yaw at first contact and ±15 Nm tibia bending moment in the preceding 30 ms). Neither paragraph appears among the 1,281 saved candidates. These are **confirmed extraction omissions**. Filtered candidates R-0899, R-0900, R-0905, R-0906, and R-0907 cover distinct bumper test locations/spacing and are exact-source matches. R42 R-0399 and R-0421 are also exact-source matches. R42 candidates R-0412, R-0413, R-0416, and R-0419 were *not* recovered because the source says `should` and the candidate changed this to `shall`.

The baseline includes 30 R48 requirements for front fog, cornering, manoeuvring and answer-back lamp functions (9 + 11 + 6 + 4). Their presence in this bumper is not established by the spec. These are possible precision costs, not confirmed false positives. No baseline requirements were removed in the candidates. A separate citation issue exists: R10 requirement R-0029 cites page 10, while the quoted ESA emissions method starts on page 11. The baseline was left unchanged.

## Validated local candidates

| Candidate | Requirements | Added | Removed | SHA-256 | Official validator |
|---|---:|---:|---:|---|---|
| `baseline.json` | 470 | 0 | 0 | `9a4032c68f56ef036fea417fdcf12ba9dc0f8388d068119fe1304cd6f1ae1729` | Strict OK |
| `verified-recovery.json` | 479 | 9 | 0 | `7d97af7fbececfdba7d5e12f878b023eaab66b7c42ccfb132cc05585098232f2` | Strict OK |
| `recall-recovery.json` | 490 | 20 | 0 | `542db8084e5b7085ee4966fafe346cd000897700dc79017bb936e3e8033e0a53` | Strict OK |

The 9 conservative additions are seven R127 and two R42 requirements. The broader candidate adds 11 conditional R26, R48, R148, and additional R127 clauses, some overlapping GTR9 test procedures. Every addition's original quote occurs on its cited PDF page. `artifacts/evaluations/heldout-f2-20261025/change-ledger.json` records its ID, text, exact source, original candidate confidence, applicability condition, and reason. The three submission JSONs are read-only; no existing submission was overwritten. The `main-f2` deterministic tests passed (3/3).

## Recommendation boundary

First match the actual platform upload filename/hash to one of the saved files. If it is `heldout-v1`, the safest manual trial is `verified-recovery.json`: its 9 additions have direct source support and narrow bumper-test relevance, with less risk from unspecified lamp and aerial variants. Its gain is unmeasured, and the already exported GTR9 yaw condition may overlap one R127 addition. Because the leaderboard uses the last valid upload, the candidate should not replace the current score without deliberate acceptance of that risk. If the scored file was the older 575-requirement dry run, neither candidate should be uploaded; the analysis must be rebased on that exact JSON.
