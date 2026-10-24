# Measured results on the worked examples

All numbers are from the public development cases. Requirement-level numbers come from an **internal LLM judge**
(`certi/evaluate.py`: Claude matches our requirements one-to-one against `expected.json` per regulation, on same
scope/condition/constraint). It is not the platform score and varies by about ±0.02 between judgings. Regulation and
page level come from the organizer's `tools/score_local.py`.

Granularity few-shot examples were taken from UN R150 and UN R10 only (`prompts/granularity_examples.md`), so
**UN R148 and UN R48 (119 of 190 expected requirements) are a clean check**.

## Main goal: dev-rear-lamp (190 expected requirements in 4 regulations)

| Run | Configuration | Regs P / R | Pages P / R | Req. P / R | Req. F2 | Exported | Cost |
|---|---|---|---|---|---|---|---|
| dev-v1-noaudit | prompt v1, threshold 0.15, regs incl. p<0.5 | 0.80 / 1.00 | 0.55 / 0.96 | 0.33 / 0.81 | 0.63 | 461 | $7.9 |
| dev-v2-audit | prompt v2 + omission audit, threshold 0.5 | 1.00 / 1.00 | 0.65 / 0.94 | 0.44 / 0.81 | 0.69 | 346 | $13.3 |
| dev-v3 | prompt v3 (conditional-probability tweak) | 1.00 / 1.00 | 0.65 / 0.94 | 0.40 / 0.78 | 0.66 | 371 | $7.7 |
| **dev-v2-frozen** | **prompt v2, no audit, threshold 0.5** (frozen) | **1.00 / 1.00** | **0.65 / 0.94** | **0.44 / 0.79** | **0.68** | 343 | $0 (cache) |

Clean subset (frozen run): UN R148 P 0.46 / R 0.75, UN R48 P 0.48 / R 0.77.

### What we measured and changed

- **Regulation selection**: v1 included UN R26 (model probability 0.45) → 8 extra requirements, regulation precision
  0.80. Rule changed to "extract regulations with probability ≥ 0.5": 4/4, no extras. Legacy R7 / R23 / R3 were
  correctly rejected (their transitional provisions say approvals cease after UN R148 / R150).
- **Export threshold**: sweep over all 602 judged candidates of dev-v2: threshold 0 → F2 0.60, 0.3 → 0.63,
  0.4 → 0.66, **0.5 → 0.69**, 0.6 → 0.64. The model probability is not calibrated; 0.5 is the measured optimum.
- **Independent omission audit**: added 63 candidates, **3 correct** (5%), +40% cost. Off by default (CLI `--audit`).
- **Prompt v2** (aggressive splitting, conditional permissions, variant provisions): precision 0.33 → 0.44 at the
  same recall. Prompt v3 did not help (within noise or worse), so it was reverted.
- **Recall ceiling**: even all candidates reach recall 0.86. Remaining misses are table rows bundled into one
  requirement (UN R10 test pulses), optional-variant provisions rated below the threshold, and judge mismatches of
  equivalent wording.
- **Precision**: most "extras" are real obligations of the selected sections that the expert list does not contain
  (e.g. "the colour of the light emitted by the reversing lamp shall be white"). They are cheap for an engineer to
  discard, but they cost platform precision.

## Parser

`python -m certi.eval_parser`: 187/190 gold (regulation, paragraph) pairs found on the gold page (98.4%); the 3
misses are composite labels such as "5.1.4.4.1. Table 3". All 92 PDFs in the index parse.

## Sub-goal: subgoal-dev (UN R175 0.1.0 → 1.0.0, 94 old requirements, 24 expected changes)

| Metric (internal, lexical matcher) | Value |
|---|---|
| Flagged modified/removed requirements found | **7/7** (no false flags) |
| Change type correct | **7/7** |
| Added requirements matched | 15/17 (the two misses are equivalent wording our strict matcher rejects) |
| Overall recall / precision | 0.92 / 0.81 |
| Cost | < $1 |

The deterministic alignment (source sentence located anywhere in the new text, word diff, editorial normalisation
of "6 seconds" → "6 s" and "70%" → "70 per cent") alone reproduces the 7 expected flags exactly. Claude only rewrites
the modified texts and splits new text into atomic added requirements.

## Platform scores (worked examples, uploaded 24 Oct)

| Upload | Platform result |
|---|---|
| Main, dev-v2-frozen (343 reqs) | Requirements P 35.0% / R 63.2% / F1 45.0% / **F2 54.4%**; pages P 64.6% / R 94.3%; regulations 100% / 100% |
| Sub-goal, subgoal-dev v1 (27 changes) | Flag recall 79.2%, flag precision 70.4%, change accuracy 66.7% |

The platform judge is stricter than our internal judge (recall 0.63 vs 0.79). A lexical proxy (one-to-one matches with
word similarity >= 0.7) tracks the platform closely (P 0.32 / R 0.58 on the same file) and is now used for offline tuning.

Tuning with that proxy (no further uploads needed):
- Export threshold sweep 0 / 0.3 / 0.4 / **0.5** / 0.6 / 0.7: proxy F2 0.43 / 0.44 / 0.47 / **0.50** / 0.48 / 0.46, so 0.5 stays.
- Dropping annex requirements lowers proxy F2 (0.50 to 0.47), so annexes stay.
- Prompt v4 (subject first, never specialise to the product, keep all qualifiers): proxy F2 0.48 vs 0.50 for v2. Reverted.
- Sub-goal: the 7 modified/removed flags are right, so the platform gap is in `added` items. The added-extraction prompt
  now teaches the expected patterns ("The procedure for ... shall be to ...", named actor, one requirement per
  "shall"/"may" clause). This is pending a platform upload of artifacts/subgoal/subgoal-dev-v4/changes.json.
