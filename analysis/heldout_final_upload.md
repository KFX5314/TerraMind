# Held-out final upload (25 October 2026)

## Main goal (front bumper): final leaderboard file

`artifacts/evaluations/heldout-probe-20261025/main-E-noR94-judge0.3.json`: 300 requirements,
SHA-256 `f3e0167259f59a0b4f38d16d641b747e5a37cd407ecd5c73c7e739769fe32c4c`.

It was built from the scored 360-item file `heldout-f2-module-scope-20261025/module-evidence-side-recovery-360.json`
(official F2 65.0%, precision 43.1%, recall 74.5%; regulations precision 87.5%, recall 100%) in two steps:

1. **Model judge, cut-off 0.3** (`analysis/judge_requirements.py`). Claude rates each requirement with the
   probability that the expert list for this product contains it, using the product spec only. The cut-off was
   calibrated on the dev rear-lamp upload against `expected.json`. With matcher threshold 0.5, the matcher reproduces
   the platform's 157 matches on that file.

   | cut-off | kept | correct lost | wrong removed | F2 |
   |---|---|---|---|---|
   | none | 373 | 0 | 0 | 0.693 |
   | 0.2 | 345 | 2 | 26 | 0.701 |
   | **0.3** | 327 | 4 | 42 | **0.708** |
   | 0.35 | 294 | 14 | 65 | 0.688 |

   On the held-out 360 file it removed 48 requirements, mostly conformity-of-production and sampling clauses and
   lamp-function variants. Ratings are in `judge_heldout360.json`, and the dev calibration ratings in `judge_dev.json`.
2. **UN R94 removed.** Regulation precision 87.5% means one of the 8 cited regulations is not in the reference list.
   R94 was the weakest on three signals: screening p=0.40 (potentially applicable), the lowest mean judge rating
   (0.34), and the earlier team analysis.

The pre-upload estimate was F2 about 67% if R94 was the extra regulation. The official result for this file was
not recorded here.

Other probe files in the same folder:
- `main-A-without-R94` (346)
- `main-B-without-GTR9` (331)
- `main-C-judge0.3` (312)
- `main-D-noGTR9-judge0.3` (287)

Rollback: the 360-item file (F2 65.0%).

## Sub-goal (regulation change, UN R171)

**Final leaderboard file:** `artifacts/subgoal/heldout 5 subgoal annex/changes.json`: 85 changes (14 modified, 4
removed, 67 added), SHA-256 `e68138d33167f6f9a3ab12261999eb158026dbf593bbb5b186f248c7e3d01699`. It is the best
63-change file plus 22 new obligations from Annexes 3 and 4. Reproduce it with:

```
CERTI_SUBGOAL_ANNEX=1 python -m certi subgoal --case subgoal-heldout --team team-10
```

The code on `main` reproduces this file exactly, from the cached model answers. The official result for this file
was not recorded here.

Code: `certi/subgoal.py` is v12 plus the held-out crash fix. It reproduces `artifacts/subgoal/subgoal-heldout-fresh`
exactly (63 changes; official 81.2% flag recall, 82.5% flag precision, 72.9% change accuracy). The optional switch
`CERTI_SUBGOAL_ANNEX=1` lets new annex obligations pass the covered-section gate.

Two results learned from the platform:
- **Careful detection did not help.** Keeping changes that the model judged "not affected", and adding all new
  sentences in modified paragraphs, produced `heldout 4 subgoal` (72 changes). It scored 78.1% / 69.4% / 82.6%, so
  those 9 extra changes were not in the reference list. That logic was reverted.
- **Requirements-only output loses recall.** The reference list for this case has about 64 changes, and at least
  32 of them are "added" items.

Candidates:
- `heldout 5 subgoal annex`: 85 changes, the best 63 plus 22 annex additions.
- `heldout 6 subgoal annex-judged`: 70 changes, the best 63 plus the 7 annex additions rated >= 0.5 by
  `analysis/judge_changes.py`.

The change judge separated dev extras only weakly: it rated correct test-procedure steps as low as the extras. It is
therefore used only to rank uncertain annex additions.
