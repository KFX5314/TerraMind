# Historical runs: main objective and amendment sub-goal

Reviewed 24 October 2026 using the saved submissions in `artifacts/runs`, amendment outputs in `artifacts/subgoal`, the public expected files, and the current implementation. All comparisons were local. No model calls, generation reruns, platform submissions, or application/configuration changes were made. Diagnostic script: `tmp/compare_history.py`; detailed output: `tmp/compare_history_output.txt` (ignored local files).

## What the numbers establish

The platform figures below are from `docs/results.md`, not a newly fetched platform response. Recomputed local requirement scores use the current lexical matcher and must not be mistaken for semantic/platform scores.

| Main run | Exported | Local proxy matches / 190 | Proxy precision | Proxy recall | Proxy F2 |
|---|---:|---:|---:|---:|---:|
| dev-v1-noaudit | 461 | 116 | 25.2% | 61.1% | 47.5% |
| dev-v2-audit | 346 | 119 | 34.4% | 62.6% | 53.8% |
| dev-v2-frozen | 343 | 119 | 34.7% | 62.6% | 53.9% |
| dev-v3 | 371 | 114 | 30.7% | 60.0% | 50.4% |
| dev-v4 | 367 | 120 | 32.7% | 63.2% | 53.2% |
| dev-v6 | 363 | 131 | 36.1% | 68.9% | 58.3% |
| dev-v6-newimg | 347 | 127 | 36.6% | 66.8% | 57.4% |

Saved platform main-goal F2 improved from 54.4% (v2-frozen) to 66.8% (v6-newimg). The proxy underestimates the latter materially. Differences of a few proxy matches are leads for source review, not evidence that the corresponding platform score improved or regressed.

For the sub-goal, the local scorer returns 22/24 total matches for v1, v4, and v5. V1 has 27 changes, v4/v5 have 28, so local precision falls from 81.5% to 78.6% with unchanged nominal recall of 91.7%. Saved platform recall nevertheless improves from 79.2% to 83.3%, and change accuracy from 66.7% to 68.4%. This exposes weaknesses in local evaluation, detailed below.

## 1. Amendment alignment loses the tail of a changed provision

**Priority: highest.** `certi/subgoal.py:best_window`, `locate`, and `analyse`.

For R-021 / paragraph 5.1.5, v5's stored `new` alignment stops after condition (d)(i). The complete cached new paragraph continues with changed conditions (d)(ii) onwards, including vehicle, wall, and pedestrian obstacle cases. The parser has this text; the selected alignment window does not. Maximizing similarity to the old source prefers a prefix and omits heavily amended content.

The subsequent deterministic patch therefore cannot apply amendments that were absent from its input. R-021's stored `det_new_text` retains old material and reaches beyond the export limit; the actual submission ends mid-sentence at exactly 2,000 characters. The expected replacement is 1,894 characters. Its shorter wording is not a license to copy gold: recover the complete aligned provision and preserve the relevant conditions within the schema limit.

Recommended implementation:

- Align provision identity using heading hierarchy, neighboring clauses, and renumbering anchors before selecting sentence spans.
- Preserve the complete matched provision's amended tail, rather than treating its highest-similarity prefix as complete.
- Track changed spans and require each to be accounted for in the updated requirement or an explicit unrelated-change disposition.
- Replace `[:2000]` truncation with length-aware rewriting and verification of critical conditions, values, exceptions, and references. Preserve the full internal representation.

Measure tail-clause coverage and critical-fact preservation. Include synthetic cases where a long paragraph changes at its end.

## 2. New obligations in a new scope are suppressed as old text

**Priority: highest.** `certi/subgoal.py`, new-text detection around lines 300–325.

The expected added step at new paragraph 6.6.2.2(b), "Hold the vehicle stationary and select the corresponding driving direction", is present in the cached new paragraph and the saved group's context. It is absent from the group's `new` / `new_text`, so the extraction model never gets it as eligible new text.

The same sentence occurs in old paragraph 6.5 and new 6.6.1.2, under the stationary test procedure. Global lexical old-text matching does not distinguish its additional occurrence under the new creeping-vehicle procedure. The current code also suppresses every segment of a paragraph that contains a modified target, and limits additions to scopes represented by the old requirements. These are further general recall risks even when they do not produce another confirmed dev miss.

Use context-sensitive alignment with occurrence accounting. Represent an obligation as actor + action + conditions + procedure scope + source occurrence. Reused wording in an additional procedure can introduce an additional obligation. Subtract covered obligation spans, rather than whole paragraphs. Scan new unmatched sections for relevant additions, with applicability decisions recorded explicitly.

## 3. Sub-goal local metrics credit the wrong actions

**Priority: highest for trustworthy iteration.** `certi/subgoal_score.py`.

The current scorer awards full credit to a modified item when its old ID and change type match. It never checks `new_text` or `reason`, so R-021's truncated replacement still counts as correct.

For additions, greedy matching plus a paragraph bonus matches expected "hold the vehicle stationary" to submitted "release the braking system" with a score of approximately 0.736. It then matches the expected release step to the accelerator-operation step at approximately 0.555, exhausting a candidate that exactly matches a later expected item. These actions are different even though their boilerplate and paragraph match.

Introduce separate measures for affected-ID recall, change-type accuracy, replacement-text correctness, amendment-span coverage, and addition correctness. Resolve one-to-one assignments globally after checking actor/action/condition/value compatibility. A paragraph bonus must not compensate for the wrong action. Exact matches should not be consumed by earlier weaker pairs.

This also explains why the prior claim that both added misses are merely equivalent wording is unsupported by the current scorer. At least one required step is actually absent.

## 4. Granularity needs a coherent policy in both objectives

**Priority: high.** Extraction prompts and requirement representation.

The sub-goal expected file bundles several things the pipeline splits:

- The two ACPE intervention exceptions: expected one addition; v5 two.
- The pedestrian target's construction and sensor representativeness: expected one; v5 two.
- Forward/rearward vehicle reference points: expected one; v5 two. Neither half alone reaches the local match threshold for the combined expected text.

Conversely, expected procedure steps at 6.6.2.2 are individually assessed. "Split everything" and "one requirement per paragraph" both fail on this example.

Use a clause tree that preserves the parent actor, condition, lists, and dependent predicates. Keep coordinated properties/alternatives of a single obligation together when separately emitting them loses the obligation's meaning; split independently assessable commands. Retain internal children for UI checklists and evidence. Export each obligation once, at the declared granularity.

Do not hardcode the dev paragraph numbers or mechanically merge every list: independent procedure steps must remain distinct. Apply the same policy to main-goal table outputs: the R150 minimum-RI expected requirement combines measurement points which the current output fragments by divergence angle.

## 5. Main-goal extraction is unstable across runs

**Priority: high.** Add regression accounting and provenance.

Relative to v2-frozen, v6-newimg gains 22 proxy-matched golden IDs and loses 14, for a net gain of eight. Across the six complete four-regulation runs, the union of proxy-matched expected IDs is 142; the latest run matches 127. This is evidence for investigating instability, not justification for taking the union of all generated outputs. Such a union would also accumulate false positives.

V6 and v6-newimg use the same saved configuration but different product profiles and output 363 versus 347 requirements. Their proxy scores differ by four matches. The saved inputs reference the image path without an image content hash/snapshot, so exact reproduction of the historic visual input is limited. Do not attribute the difference solely to the image or solely to model randomness.

Record immutable hashes/snapshots of image, spec, corpus, parser, prompt and config. Freeze the product profile while comparing extractors. Report per-regulation and per-source-obligation regressions, with losses assigned to parsing, extraction, applicability, deduplication, or export. Recheck only uncovered clauses and unresolved obligations with an independent verifier; do not blindly merge previous outputs.

## 6. Main-goal losses are not mainly a threshold problem

**Priority: high.** Existing dedupe finding remains the strongest inexpensive main-goal fix.

Latest-run funnel under the same local proxy:

| Stage | Candidates | Matches / 190 | Proxy recall |
|---|---:|---:|---:|
| All raw candidates, any probability | 653 | 142 | 74.7% |
| Raw candidates at probability >= 0.5 | 373 | 135 | 71.1% |
| After current dedupe, any probability | 592 | 133 | 70.0% |
| Current export after dedupe, >= 0.5 | 347 | 127 | 66.8% |

These are matcher outcomes, not an exact semantic decomposition. They nevertheless show why lowering the threshold alone cannot solve the problem: even exporting all raw candidates only reaches 142 local matches while adding hundreds of extras. The retained-candidate threshold sweep gives F2 55.1% at 0.4, 57.4% at 0.5, and 55.5% at 0.6. Keep 0.5 as the baseline until a broader evaluation supports changing it.

G-0103 is an exact-text raw candidate with probability 0.85 that is absent from latest matches after postprocessing. Other confirmed dedupe losses were detailed in `IMPROVEMENT_REVIEW.md`. Fix that structural loss before adding generation passes.

Separate confidence in source entailment from applicability and product-variant uncertainty. A conditionally relevant requirement can be correct even if its condition has not been confirmed; preserve the condition and distinguish it in the UI/export policy. Do not globally lower thresholds to rescue a handful of dev examples.

## 7. R148 and tables remain targeted main-goal opportunities

Latest per-regulation proxy recall is R10 71.9%, R148 57.1%, R150 74.4%, R48 69.6%. R148 is the largest local recall gap: 36/63 matched. This is an investigation priority, not a reason to give it a special gold-derived threshold.

The R148-only saved experiment supports smaller sections modestly: 16k to 8k changes local matches from 37 to 38 and F2 from 51.8% to 52.8%. It does not justify making every chunk smaller. Keep complete clauses and their parent conditions, table headers, footnotes and references together; size chunks by structure and token budget.

Preserve table values with units, row/column headers, category and polarity. Validate a structured constraint representation before rendering requirement text. For R150, raw candidates show only a partial set of angle-dependent limits relative to some combined expected requirements. For R10, already extracted table distinctions can also be lost during dedupe. Audit extraction and postprocessing separately.

## Experiment order and generalization controls

1. Repair sub-goal evaluation; add targeted fixtures for wrong-action matches, changed tails, context reuse, and bounded exports.
2. Repair main-goal dedupe and sub-goal full-provision alignment/export handling.
3. Add scope-aware change detection and changed-span accounting.
4. Introduce one consistent granularity policy and structured table facts.
5. Run targeted verification only for ambiguous alignment, conflicting facts, uncovered clauses, and conditional applicability.

Develop using existing expected files only in evaluation. Never prune solely because a gold file omits a paragraph: for example, v5 includes obligations from 6.3.2 and 6.5.4 absent from the gold additions, and omission alone does not establish they are invalid.

Use synthetic amendments in unfamiliar provisions: identical text in two scopes, renumbering, full deletion, changed signs/units/negation, added table rows and tail conditions, editorial-only changes, and inheritance of parent exceptions. Also evaluate a genuinely unseen product/version pair when available. Repeatedly tuned R148 is no longer an untouched holdout even though the few-shot file contains no R148 examples.

Success should mean more correct obligations and amendments with preserved conditions, not merely a higher lexical score on these two worked examples. No quantified leaderboard gain is established until a changed implementation is evaluated and submitted.
