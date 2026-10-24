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

## Round 2 (after the first platform scores): comparing our rear-lamp output with expected.json

Calibrated offline metrics (`certi/proxy.py`, `certi/evaluate.py`):
- Lexical proxy: one-to-one matches with word similarity >= 0.65 reproduces the platform (119 vs 120 matches, P 0.347 / R 0.626 vs 0.350 / 0.632). Conservative: does not credit reordered clauses.
- Strict LLM judge (same scope, condition and constraint; bundling or narrowing = no match): 111 matches, P 0.324 / R 0.584.

Where the 190 expected requirements went (frozen v2 file, lexical proxy): 127 matched; 3 filtered by the threshold;
**51 have a close candidate with different wording or granularity**; 9 not extracted (mostly table rows). The 51 are
counted as extras too, so fixing them helps precision and recall together. On UN R148 the causes were: ~10 clause order
only (gold: "The approval marking shall be placed on both ... if the outer lens ..."), ~10 under-splitting (gold makes one
requirement per "shall", e.g. 4.5.5 has 4), ~5 skipped content (telegraphic "Colour: ... shall be red" entries,
conformity-of-production tolerance limits, annex compliance statements), ~3 gold paraphrases.
Of the 224 extras, 163 come from paragraphs the expert list does not touch at all; the per-probability hit rates
(p=0.8: 50 %, 0.7: 22 %, 0.6: 17 %, 0.5: 21 %) are all above the F2 break-even (~11 %), so the threshold stays at 0.5.

Changes made (architecture):
1. Extraction prompt v5/v6 (`certi/extract_prompt.py`): the requirement is the source sentence copied with a closed list
   of allowed edits; one requirement per "shall" predicate (incl. relative clauses and consecutive "shall" sentences);
   telegraphic entries become sentences; CoP tolerance limits and annex compliance statements included. The model also
   returns the verbatim source sentence; code computes a fidelity score (share of source words kept) shown in the UI.
2. Structured tables (`certi/tables.py`): PyMuPDF `find_tables` with cell text rebuilt from word boxes, rendered as
   markdown and attached to the owning paragraph, so table rows become one requirement each (R10 6.9.1 test pulses).
3. Sections of 8 000 characters instead of 16 000: the model overlooked plain "shall" sentences in 44-paragraph sections.
4. Sub-goal: `new_text` of modified requirements is produced by applying the old->new source diff to the old requirement
   text in code (`certi/subgoal_apply.py`); the model is only used when an edited phrase cannot be anchored. All 6
   modified items on dev are now deterministic (similarity to the expected text: 0.72-0.97). Heading titles merged into
   paragraph text are stripped before diffing; the locator no longer caps the search window for long requirements.

Measured on UN R148 only (63 expected; clean: no few-shot example comes from R148):

| Config | Candidates | Exported | Lexical proxy F2 @0.5 | Strict judge matched / F2 |
|---|---|---|---|---|
| v2 frozen | 153 | 103 | 0.479 | 35 / 0.493 |
| v5 | 137 | 89 | 0.484 | 40 / 0.587 |
| v6, 16k sections | 158 | 105 | 0.518 | - |
| **v6, 8k sections** | 166 | 108 | **0.528** | **48 / 0.667** |

### Platform after round 2 (24 Oct, new labelled rear-lamp drawing)

| Upload | Platform result |
|---|---|
| Main, dev-v6-newimg (347 reqs) | Requirements P 42.7% / R 77.9% / **F2 66.8%** (was 54.4%); pages P 62.1% / R 96.2%; regulations 100% |
| Sub-goal, subgoal-dev-v5 (28 changes) | Flag recall **83.3%** (was 79.2%), flag precision 71.4%, change accuracy 68.4% |

## Round 3 (after Codex's IMPROVEMENT_REVIEW / METRICS_ABLATION / HISTORICAL_RUN_REVIEW)

Already in main from the review (commit e787511): exact, paragraph-aware dedupe (no fuzzy merging of different limits,
pulses or paragraphs); sub-goal occurrence-aware alignment, full-tail recovery, bounded rewrites.

Fixed in this round:
- Sub-goal tokenizer keeps signs and inequalities ("-10 V" vs "10 V", "≤" vs "≥" are now different).
- Fidelity score drops to <= 0.3 when negation flips ("shall not emit" vs "shall emit" was 1.0).
- Screening retries regulations the model skipped; an unresolved one now defaults to probability 0.5 (kept) instead of 0.3 (silently dropped).
- Spend counter resets per run, so MAX_RUN_USD is a per-run cap also inside the web server.
- Extraction sections start with their out-of-section parent clauses as context (`CERTI_CONTEXT_PARENTS`, default on).

| Run | Generation | Exported | Proxy matches / 190 | Proxy F2 | Cost |
|---|---|---|---|---|---|
| dev-v6-newimg (platform F2 66.8%) | v6 | 347 | 127 | 0.574 | - |
| dev-v6-dedupe (= Codex main-patched) | same candidates, new dedupe | 373 | 135 | **0.596** | $0 |
| dev-v7-context | fresh, + parent context | 394 | 136 | 0.589 | $7.87 |

Parent context shows no measurable offline gain (within run-to-run noise); a platform upload decides.
Sub-goal: Codex's Sonnet-generated `subgoal-dev-v6-sonnet` is stored for a platform check; the current best upload
remains subgoal-dev-v5 (83.3% / 71.4% / 68.4%).
